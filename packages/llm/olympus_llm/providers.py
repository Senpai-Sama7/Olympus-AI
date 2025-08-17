from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
import os

class LLMProvider(ABC):
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: Optional[int]) -> str:
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], model: str, temperature: float) -> AsyncGenerator[str, None]:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: Optional[str] = None):
        super().__init__("ollama")
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.connect_timeout = float(os.environ.get("CONNECT_TIMEOUT_SEC", "10"))
        self.request_timeout = float(os.environ.get("REQUEST_TIMEOUT_SEC", "30"))

    async def chat(self, messages: List[Dict[str, str]], model: str, temperature: float, max_tokens: Optional[int]) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.request_timeout, connect=self.connect_timeout)
        ) as client:
            resp = await client.post(f"{self.base_url.rstrip('/')}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                if "message" in data and isinstance(data["message"], dict):
                    return str(data["message"].get("content", ""))
                if "choices" in data and data["choices"]:
                    return str(data["choices"][0].get("message", {}).get("content", ""))
                if "response" in data:
                    return str(data["response"])  # generate endpoint compatibility
            return str(data)

    async def stream_chat(self, messages: List[Dict[str, str]], model: str, temperature: float) -> AsyncGenerator[str, None]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.request_timeout, connect=self.connect_timeout)
        ) as client:
            async with client.stream("POST", f"{self.base_url.rstrip('/')}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    yield line
