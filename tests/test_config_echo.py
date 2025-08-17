from fastapi.testclient import TestClient
from olympus_api.main import app


def test_config_echo(monkeypatch):
	monkeypatch.setenv("ENV", "dev")
	monkeypatch.setenv("DEV_ALLOWED_ORIGINS", "http://localhost:3000")
	client = TestClient(app)
	resp = client.get("/v1/config")
	assert resp.status_code == 200
	data = resp.json()
	assert data["ENV"] in ("dev", "test", "prod")
	assert isinstance(data.get("DEV_ALLOWED_ORIGINS", []), list)
