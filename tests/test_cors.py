from fastapi.testclient import TestClient
from olympus_api.main import app


def test_cors_dev(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("DEV_ALLOWED_ORIGINS", "http://localhost:3000")
    client = TestClient(app)
    r = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)


def test_cors_prod_disallow(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("PROD_ALLOWED_ORIGINS", "https://app.example.com")
    client = TestClient(app)
    r = client.options(
        "/health",
        headers={"Origin": "http://malicious", "Access-Control-Request-Method": "GET"},
    )
    # Many frameworks return 200 but without CORS headers; we assert lack of ACAO header
    assert "access-control-allow-origin" not in {
        k.lower(): v for k, v in r.headers.items()
    }
