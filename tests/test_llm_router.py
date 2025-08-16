import asyncio

from olympus_llm.router import LLMRouter, ModelNotAllowedError


def run(coro):
	return asyncio.get_event_loop().run_until_complete(coro)


def test_allowlist_enforced(monkeypatch):
	monkeypatch.setenv("OLLAMA_MODEL_ALLOWLIST", "llama3:8b")
	router = LLMRouter(base_url="test://stub")
	try:
		run(router.chat(messages=[{"role": "user", "content": "hi"}], model="bad-model"))
		assert False, "expected ModelNotAllowedError"
	except ModelNotAllowedError:
		pass


def test_stub_response(monkeypatch):
	monkeypatch.setenv("OLLAMA_MODEL_ALLOWLIST", "llama3:8b")
	router = LLMRouter(base_url="test://stub")
	resp = run(router.chat(messages=[{"role": "user", "content": "hi"}], model="llama3:8b"))
	assert resp == "stub-response"


def test_stream_stub(monkeypatch):
	monkeypatch.setenv("OLLAMA_MODEL_ALLOWLIST", "llama3:8b")
	router = LLMRouter(base_url="test://stub")
	chunks = []
	async def collect():
		async for c in router.stream_chat(messages=[{"role": "user", "content": "hi"}], model="llama3:8b"):
			chunks.append(c)
	run(collect())
	assert chunks == ["hello", "world"]
