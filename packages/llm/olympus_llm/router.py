# packages/llm/olympus_llm/router.py
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, Optional, Tuple, List, AsyncGenerator

import requests

from packages.memory.olympus_memory.db import MemoryDB
from . import llamacpp as llama_provider

# --------- Config (env) ----------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

ENABLE_CLOUD = os.getenv("OLY_ENABLE_CLOUD", "false").lower() == "true"  # default off
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DAILY_USD_BUDGET = float(os.getenv("OLY_DAILY_USD_BUDGET", "0.0"))  # 0 => disable cloud
CACHE_TTL_MS = int(os.getenv("OLY_LLM_CACHE_TTL_MS", "1800000"))  # 30m
DAILY_TOKEN_BUDGET = int(os.getenv("OLY_DAILY_TOKEN_BUDGET", "0"))  # 0 => unlimited for llama.cpp


def _today_key() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _hash_prompt(prompt: str, system: Optional[str], tools: Optional[Dict[str, Any]]) -> str:
    h = hashlib.sha1()
    h.update(prompt.encode())
    if system:
        h.update(system.encode())
    if tools:
        h.update(json.dumps(tools, sort_keys=True).encode())
    h.update(OLLAMA_MODEL.encode())
    return f"llm:{h.hexdigest()}"


class BudgetExceeded(Exception):
    pass


class ModelNotAllowedError(Exception):
    pass


class LLMRouter:
    """
    Local-first LLM router with async chat APIs.
    Supports a special base_url 'test://stub' used by tests.
    """

    def __init__(self, base_url: Optional[str] = None, db: Optional[MemoryDB] = None):
        self.base_url = base_url or OLLAMA_URL
        self.db = db or MemoryDB()

    # --------------- Budget ----------------
    def _get_spend(self) -> float:
        key = f"budget:{_today_key()}"
        item = self.db.cache_get(key)
        if not item:
            return 0.0
        return float(item["value"]["usd"])

    def _add_spend(self, delta_usd: float):
        key = f"budget:{_today_key()}"
        cur = self._get_spend()
        new_v = {"usd": round(cur + delta_usd, 6)}
        self.db.cache_put(key, new_v, ttl_ms=86_400_000)  # 24h

    def _ensure_budget(self, need_usd: float):
        if DAILY_USD_BUDGET <= 0:
            raise BudgetExceeded("Cloud disabled (budget=0)")
        if self._get_spend() + need_usd > DAILY_USD_BUDGET:
            raise BudgetExceeded("Daily LLM budget exceeded")

    # --------------- Token budget (llama.cpp) ----------------
    def _get_token_spend(self) -> int:
        key = f"budget_tokens:{_today_key()}"
        item = self.db.cache_get(key)
        if not item:
            return 0
        return int(item["value"].get("tokens", 0))

    def _add_token_spend(self, delta_tokens: int):
        key = f"budget_tokens:{_today_key()}"
        cur = self._get_token_spend()
        self.db.cache_put(key, {"tokens": int(cur + delta_tokens)}, ttl_ms=86_400_000)

    def _ensure_token_budget(self, need_tokens: int):
        if DAILY_TOKEN_BUDGET <= 0:
            return
        if self._get_token_spend() + need_tokens > DAILY_TOKEN_BUDGET:
            raise BudgetExceeded("Daily LLM token budget exceeded")

    # --------------- Cache -----------------
    def _cache_get(self, key: str) -> Optional[str]:
        item = self.db.cache_get(key)
        return None if not item else item["value"]["text"]

    def _cache_put(self, key: str, text: str):
        self.db.cache_put(key, {"text": text}, ttl_ms=CACHE_TTL_MS, meta={"model": OLLAMA_MODEL})

    # --------------- Token/$ estimate (rough) ---------------
    @staticmethod
    def _approx_tokens(text: str) -> int:
        # not exact; good enough for budget smoothing
        return max(1, int(len(text) / 4))

    @staticmethod
    def _estimate_usd(model: str, tokens_in: int, tokens_out: int) -> float:
        # simple defaults; override via env if you want exact pricing
        # e.g., 4o-mini ~$0.150 / 1M input, $0.6 / 1M output => $0.00000015/tok in, $0.0000006/tok out
        in_rate = float(os.getenv("OPENAI_USD_PER_INPUT_TOKEN", "0.00000015"))
        out_rate = float(os.getenv("OPENAI_USD_PER_OUTPUT_TOKEN", "0.00000060"))
        return tokens_in * in_rate + tokens_out * out_rate

    # --------------- Public -----------------
    def generate(self, prompt: str, system: Optional[str] = None, tools: Optional[Dict[str, Any]] = None) -> str:
        key = _hash_prompt(prompt, system, tools)
        cached = self._cache_get(key)
        if cached:
            return cached

        # Try local (Ollama)
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "")
            self._cache_put(key, text)
            return text
        except Exception:
            # fall through to cloud if allowed
            pass

        # Cloud fallback (OpenAI)
        if ENABLE_CLOUD and OPENAI_API_KEY:
            tokens_in = self._approx_tokens(prompt)
            tokens_out = 800  # cap
            est = self._estimate_usd(OPENAI_MODEL, tokens_in, tokens_out)
            self._ensure_budget(est)

            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            body = {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=60)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            # charge actual (still approximate without usage in response)
            used_in = tokens_in
            used_out = self._approx_tokens(text)
            self._add_spend(self._estimate_usd(OPENAI_MODEL, used_in, used_out))
            self._cache_put(key, text)
            return text

        # If we’re here, we failed local and cloud is disabled/unavailable.
        raise RuntimeError("LLM unavailable: Ollama failed and cloud fallback is disabled or not configured.")

    # ---------------- Async chat API (used by tests) ----------------
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> str:
        model = model or OLLAMA_MODEL
        allowlist = os.getenv("OLLAMA_MODEL_ALLOWLIST", "").strip()
        llcpp_allow = os.getenv("LLAMACPP_MODEL_ALLOWLIST", "").strip()
        if allowlist:
            allowed = {m.strip() for m in allowlist.split(",") if m.strip()}
            if model not in allowed:
                raise ModelNotAllowedError(f"Model '{model}' not allowed")
        if os.getenv("OLY_LLM_BACKEND", "").lower() in ("llamacpp", "llama.cpp") and llcpp_allow:
            allowed2 = {m.strip() for m in llcpp_allow.split(",") if m.strip()}
            if model not in allowed2:
                raise ModelNotAllowedError(f"Model '{model}' not allowed (llamacpp allowlist)")

        # Test stub behavior
        if str(self.base_url).startswith("test://stub"):
            return "stub-response"

        # If configured to use llama.cpp backend
        if os.getenv("OLY_LLM_BACKEND", "").lower() in ("llamacpp", "llama.cpp") or str(self.base_url).startswith("llamacpp://"):
            # Convert llamacpp://host:port to http URL if provided
            if str(self.base_url).startswith("llamacpp://"):
                host = self.base_url.replace("llamacpp://", "http://", 1)
                os.environ.setdefault("LLAMA_CPP_URL", host)
            # Token budget enforcement for local llama.cpp
            prompt = "\n".join(m.get("content", "") for m in messages)
            tokens_in = self._approx_tokens(prompt)
            tokens_out_cap = int(max_tokens or 800)
            self._ensure_token_budget(tokens_in + tokens_out_cap)
            text = llama_provider.chat(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
            used_out = self._approx_tokens(text)
            self._add_token_spend(tokens_in + used_out)
            return text

        # Default: use generate() path with Ollama
        prompt = "\n".join(m.get("content", "") for m in messages)
        return self.generate(prompt)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        model = model or OLLAMA_MODEL
        allowlist = os.getenv("OLLAMA_MODEL_ALLOWLIST", "").strip()
        llcpp_allow = os.getenv("LLAMACPP_MODEL_ALLOWLIST", "").strip()
        if allowlist:
            allowed = {m.strip() for m in allowlist.split(",") if m.strip()}
            if model not in allowed:
                raise ModelNotAllowedError(f"Model '{model}' not allowed")
        if os.getenv("OLY_LLM_BACKEND", "").lower() in ("llamacpp", "llama.cpp") and llcpp_allow:
            allowed2 = {m.strip() for m in llcpp_allow.split(",") if m.strip()}
            if model not in allowed2:
                raise ModelNotAllowedError(f"Model '{model}' not allowed (llamacpp allowlist)")

        if str(self.base_url).startswith("test://stub"):
            # Yield a couple of chunks as expected by tests
            yield "hello"
            yield "world"
            return

        # Fallback: no streaming implementation; yield a single full response
        text = await self.chat(messages=messages, model=model, temperature=temperature)
        yield text
