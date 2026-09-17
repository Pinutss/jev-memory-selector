import json
from datetime import datetime, timezone
from urllib.request import Request

import pytest

from jev_memory_selector import ConfigurationError, MemorySelector
from jev_memory_selector.providers import http as http_mod

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def test_local_select_content_alias():
    result = MemorySelector(provider="local").select(
        query="français",
        memories=[{"id": "m1", "content": "Répondre en français", "scope": "demo"}],
        max_tokens=32,
        scope="demo",
        now=NOW,
    )
    assert result.selected[0].id == "m1"


def test_jev_requires_keys(monkeypatch):
    for key in (
        "JEV_API_KEY",
        "JEV_BASE_URL",
        "GATEWAY_API_KEY",
        "GATEWAY_BASE_URL",
        "GATEWAY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ConfigurationError, match="JEV_API_KEY"):
        MemorySelector(provider="jev")


class _FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_jev_and_gateway_keys_stay_isolated(monkeypatch):
    calls = []

    def fake_urlopen(request: Request, timeout=None):
        headers = {key.lower(): value for key, value in request.header_items()}
        body = json.loads(request.data.decode("utf-8"))
        calls.append({"url": request.full_url, "headers": headers, "body": body})
        auth = headers.get("authorization", "")
        serialized = json.dumps(body)
        if "jev-secret" in auth:
            assert "gw-secret" not in auth
            assert "gw-secret" not in serialized
            return _FakeResponse({"scores": [{"id": "m1", "score": 0.9}]})
        if "gw-secret" in auth:
            assert "jev-secret" not in auth
            assert "jev-secret" not in serialized
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"scores": [{"id": "m1", "score": 0.8}]})
                            }
                        }
                    ]
                }
            )
        raise AssertionError(request.full_url)

    monkeypatch.setattr(http_mod, "urlopen", fake_urlopen)
    selector = MemorySelector(
        provider="jev",
        api_key="jev-secret",
        jev_base_url="https://jev.example/v1/select",
        gateway_api_key="gw-secret",
        gateway_base_url="https://gateway.example/v1",
        gateway_model="demo-model",
    )
    result = selector.select(
        query="backend",
        memories=[
            {"id": "m1", "content": "Backend FastAPI secret sk-abcdefghijklmnopqrstuvwxyz9999"}
        ],
        max_tokens=64,
        now=NOW,
    )
    assert result.selected[0].id == "m1"
    assert len(calls) == 2
    assert any("jev.example" in call["url"] for call in calls)
    assert any("chat/completions" in call["url"] for call in calls)
    for call in calls:
        assert "sk-abcdefghijklmnopqrstuvwxyz9999" not in json.dumps(call["body"])
        assert "jev-secret" not in json.dumps(call["body"])
        assert "gw-secret" not in json.dumps(call["body"])
