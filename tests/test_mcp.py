from jev_memory_selector.config import Settings
from jev_memory_selector.mcp_server import _dispatch


def test_tools_list_and_call():
    settings = Settings(provider="mock", host="127.0.0.1")
    listed = _dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, settings)
    names = [tool["name"] for tool in listed["result"]["tools"]]
    assert names == ["memory_select"]

    called = _dispatch(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "memory_select",
                "arguments": {
                    "query": "français",
                    "memories": [{"id": "language", "content": "Répondre en français"}],
                    "max_tokens": 32,
                },
            },
        },
        settings,
    )
    text = called["result"]["content"][0]["text"]
    assert "language" in text


def test_mcp_rejects_keys_in_args():
    settings = Settings(provider="mock")
    called = _dispatch(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_select",
                "arguments": {"query": "q", "memories": [], "api_key": "nope"},
            },
        },
        settings,
    )
    assert called["result"]["isError"] is True
