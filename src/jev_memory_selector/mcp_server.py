"""Serveur MCP stdio : un tool memory_select. Les clés restent dans l'env."""
from __future__ import annotations

import json
import sys
from typing import Any

from .config import Settings
from .facade import MemorySelector
from .version import __version__

PROTOCOL_VERSION = "2024-11-05"


def run_mcp(settings: Settings | None = None) -> None:
    conf = settings or Settings.from_env()
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        message = _read_message(stdin)
        if message is None:
            return
        if message.get("method") == "notifications/initialized":
            continue
        response = _dispatch(message, conf)
        if response is not None:
            _write_message(stdout, response)


def _dispatch(message: dict[str, Any], settings: Settings) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    if method == "initialize":
        return _ok(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jev-memory-selector", "version": __version__},
            },
        )
    if method == "tools/list":
        return _ok(msg_id, {"tools": [_tool_schema()]})
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name != "memory_select":
            return _ok(msg_id, _tool_error(f"outil inconnu : {name}"))
        if any(key in args for key in ("api_key", "jev_api_key", "gateway_api_key")):
            return _ok(msg_id, _tool_error("les clés ne doivent pas figurer dans les arguments"))
        try:
            result = MemorySelector(provider=settings.provider, settings=settings).select(
                query=str(args.get("query") or ""),
                memories=args.get("memories") or [],
                max_memories=args.get("max_memories"),
                max_tokens=args.get("max_tokens"),
                scope=str(args.get("scope") or "default"),
            )
        except Exception as exc:  # noqa: BLE001, surface MCP
            return _ok(msg_id, _tool_error(str(exc)))
        show_dropped = bool(settings.auth_token) or settings.host not in {"0.0.0.0", "::"}
        text = json.dumps(result.to_dict(include_dropped=show_dropped), ensure_ascii=False)
        return _ok(msg_id, {"content": [{"type": "text", "text": text}]})
    if msg_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"méthode inconnue : {method}"},
    }


def _tool_schema() -> dict[str, Any]:
    return {
        "name": "memory_select",
        "description": "Sélectionne les souvenirs pertinents sous budget de tokens.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "memories": {"type": "array", "items": {"type": "object"}},
                "max_memories": {"type": "integer"},
                "max_tokens": {"type": "integer"},
                "scope": {"type": "string"},
            },
            "required": ["query", "memories"],
        },
    }


def _ok(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _tool_error(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": True}


def _read_message(stdin: Any) -> dict[str, Any] | None:
    header = stdin.readline()
    if not header:
        return None
    if header.lower().startswith(b"content-length:"):
        length = int(header.split(b":", 1)[1].strip())
        while True:
            line = stdin.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        body = stdin.read(length)
        return json.loads(body.decode("utf-8"))
    line = header.decode("utf-8").strip()
    if not line:
        return _read_message(stdin)
    return json.loads(line)


def _write_message(stdout: Any, message: dict[str, Any]) -> None:
    raw = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stdout.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
    stdout.flush()
