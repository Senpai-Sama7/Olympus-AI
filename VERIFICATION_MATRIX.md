| ID | Feature | Command | Expected signal | Status | Evidence |
|----|---------|---------|-----------------|--------|----------|
| F1 | Test suite | `pytest -q --disable-warnings` | `16 passed` | VERIFIED | [evidence/pytest.txt](evidence/pytest.txt) |
| F2 | API health and metrics smoke | `make smoke` | `OK` | VERIFIED | [evidence/make_smoke.txt](evidence/make_smoke.txt) |
| F3 | Plan submit/run with consent | `python scripts/reality_plan_check.py` | Plan `DONE`, consent enforcement | VERIFIED | [evidence/api_plan_checks.txt](evidence/api_plan_checks.txt) |
| F4 | LLM router backend health | `curl -s http://127.0.0.1:8000/v1/llm/health` | JSON `ok: true` | UNVERIFIED | n/a |
| F5 | Agent execute reflection loop | `curl -s -X POST http://127.0.0.1:8000/v1/agent/execute ...` | Completed response after retries | UNVERIFIED | n/a |
| F6 | Streaming chat endpoint | `curl -N -X POST http://127.0.0.1:8000/v1/chat/stream ...` | Streamed SSE chunks | UNVERIFIED | n/a |
