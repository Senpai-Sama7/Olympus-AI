from fastapi.testclient import TestClient
from olympus_api.main import app


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
