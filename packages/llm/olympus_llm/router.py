import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx


class ModelNotAllowedError(Exception):
	status_code = 400

	def __init__(self, model: str) -> None:
		super().__init__(f"model not allowlisted: {model}")
		self.model = model


class ModelUnavailableError(Exception):
	status_code = 424

	def __init__(self, model: str, detail: str) -> None:
		super().__init__(detail)
		self.model = model
		self.detail = detail


class LLMRouter:
	def __init__(self, base_url: Optional[str] = None) -> None:
		self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
		allow = os.environ.get("OLLAMA_MODEL_ALLOWLIST", "")
		self.allowlist = [m.strip() for m in allow.split(",") if m.strip()] or ["llama3:8b", "llama3.1:8b"]
		self.connect_timeout = float(os.environ.get("CONNECT_TIMEOUT_SEC", "10"))
		self.request_timeout = float(os.environ.get("REQUEST_TIMEOUT_SEC", "30"))

	def _validate_model(self, model: str) -> None:
		if model not in self.allowlist:
			raise ModelNotAllowedError(model)

	async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
		model_name = model or os.environ.get("OLLAMA_MODEL", "llama3:8b")
		self._validate_model(model_name)
		if self.base_url.startswith("test://"):
			# Offline stub for tests
			return "stub-response"
		payload: Dict[str, Any] = {
			"model": model_name,
			"messages": messages,
			"stream": False,
			"options": {"temperature": temperature},
		}
		if max_tokens is not None:
			payload["options"]["num_predict"] = max_tokens
		try:
			async with httpx.AsyncClient(timeout=httpx.Timeout(self.request_timeout, connect=self.connect_timeout)) as client:
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
		except httpx.HTTPStatusError as e:
			text = e.response.text
			raise ModelUnavailableError(model_name, f"model unavailable or not pulled: {text}")
		except Exception as e:
			raise ModelUnavailableError(model_name, f"ollama not reachable: {e}")

	async def stream_chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.7) -> AsyncGenerator[str, None]:
		model_name = model or os.environ.get("OLLAMA_MODEL", "llama3:8b")
		self._validate_model(model_name)
		if self.base_url.startswith("test://"):
			# Offline stub streaming for tests
			yield "hello"
			yield "world"
			return
		payload: Dict[str, Any] = {
			"model": model_name,
			"messages": messages,
			"stream": True,
			"options": {"temperature": temperature},
		}
		try:
			async with httpx.AsyncClient(timeout=httpx.Timeout(self.request_timeout, connect=self.connect_timeout)) as client:
				async with client.stream("POST", f"{self.base_url.rstrip('/')}/api/chat", json=payload) as resp:
					resp.raise_for_status()
					async for line in resp.aiter_lines():
						if not line:
							continue
						# Ollama streams JSON lines; keep simple and yield raw lines
						yield line
		except httpx.HTTPStatusError as e:
			raise ModelUnavailableError(model_name, f"model unavailable or not pulled: {e.response.text}")
		except Exception as e:
			raise ModelUnavailableError(model_name, f"ollama not reachable: {e}")
