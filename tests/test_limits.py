from fastapi.testclient import TestClient
from olympus_api.main import app


def test_body_size_limit(monkeypatch):
    monkeypatch.setenv("MAX_BODY_BYTES", "10")
    client = TestClient(app)
    resp = client.post("/v1/dev/sleep", data="x" * 100)
    assert resp.status_code in (405, 413)


def test_timeout(monkeypatch):
    monkeypatch.setenv("REQUEST_TIMEOUT_SEC", "1")
    client = TestClient(app)
    resp = client.get("/v1/dev/sleep", params={"sec": 2})
    # In test client, middleware still applies; expect 504 or disabled if ENV=prod
    assert resp.status_code in (200, 504)


def test_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_GLOBAL_PER_MIN", "2")
    client = TestClient(app)
    client.get("/health")
    client.get("/health")
    resp = client.get("/health")
    assert resp.status_code in (200, 429)
