import pytest


def test_net_http_get_requires_consent(monkeypatch):
    # Require consent and disable auto-consent
    monkeypatch.setenv("OLY_REQUIRE_CONSENT", "true")
    monkeypatch.setenv("OLY_AUTO_CONSENT", "false")

    from apps.worker.olympus_worker.main import ToolRegistry, ToolError

    reg = ToolRegistry()
    tool = reg.resolve("net.http_get")
    with pytest.raises(ToolError):
        tool["fn"]({"url": "http://example.com"}, consent=None)
