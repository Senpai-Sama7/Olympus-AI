from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests


def _base_url() -> str:
    return os.getenv("LLAMA_CPP_URL", "http://127.0.0.1:8080")


def chat(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.2, max_tokens: Optional[int] = None) -> str:
    """
    Minimal llama.cpp HTTP client. Tries OpenAI-compatible /v1/chat/completions first,
    then falls back to /completion.
    """
    base = _base_url().rstrip("/")
    # Try OpenAI-compatible Chat Completions
    try:
        body = {
            "model": model or "llamacpp",
            "temperature": float(temperature),
            "messages": messages,
        }
        if max_tokens is not None:
            body["max_tokens"] = int(max_tokens)
        r = requests.post(f"{base}/v1/chat/completions", json=body, timeout=120)
        r.raise_for_status()
        data = r.json()
        txt = data["choices"][0]["message"]["content"]
        if isinstance(txt, str):
            return txt
    except Exception:
        pass

    # Fallback to llama.cpp native /completion
    prompt = "\n".join(m.get("content", "") for m in messages)
    body2 = {
        "prompt": prompt,
        "temperature": float(temperature),
    }
    if max_tokens is not None:
        body2["n_predict"] = int(max_tokens)
    r2 = requests.post(f"{base}/completion", json=body2, timeout=120)
    r2.raise_for_status()
    data2 = r2.json()
    # llama.cpp may return {'content': '...'} or {'completion': '...'}
    return str(data2.get("content") or data2.get("completion") or data2)

