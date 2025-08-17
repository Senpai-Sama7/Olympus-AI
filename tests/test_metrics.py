from fastapi.testclient import TestClient
from olympus_api.main import app


def test_metrics_enabled(monkeypatch):
	monkeypatch.setenv("METRICS_ENABLED", "true")
	client = TestClient(app)
	client.get("/health")
	r = client.get("/metrics")
	assert r.status_code == 200
	text = r.text
	assert "requests_total" in text
