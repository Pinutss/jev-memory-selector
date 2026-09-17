import pytest

from jev_memory_selector.api.server import authorized, handle_select, include_dropped
from jev_memory_selector.config import Settings
from jev_memory_selector.errors import ConfigurationError


def test_handle_select_local():
    settings = Settings(provider="local", redact_secrets=False, min_relevance=0.0)
    payload = handle_select(
        {
            "query": "français",
            "memories": [{"id": "m1", "content": "Répondre en français"}],
            "max_tokens": 32,
        },
        settings,
        show_dropped=True,
    )
    assert payload["selected"][0]["id"] == "m1"
    assert "dropped" in payload


def test_reject_keys_in_body():
    settings = Settings(provider="local")
    with pytest.raises(ConfigurationError):
        handle_select(
            {"query": "q", "memories": [], "api_key": "secret"},
            settings,
            show_dropped=True,
        )


def test_auth_and_dropped_visibility():
    locked = Settings(auth_token="tok", host="0.0.0.0")
    assert authorized({"Authorization": "Bearer tok"}, locked)
    assert not authorized({"Authorization": "Bearer no"}, locked)
    assert include_dropped(locked, True)
    assert not include_dropped(Settings(host="0.0.0.0"), True)
    assert include_dropped(Settings(host="127.0.0.1"), True)
