"""Command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings, load_dotenv
from .facade import MemorySelector
from .mcp_server import run_mcp


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="jev-memory", description="JEV memory selector")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Local demo, no keys, no network")
    select = sub.add_parser("select", help="Select using JEV_PROVIDER")
    select.add_argument("--file", required=True, help="JSON {query?, memories}")
    select.add_argument("--query", default=None)
    select.add_argument("--scope", default="default")
    sub.add_parser("serve", help="HTTP server /v1/select")
    sub.add_parser("mcp", help="MCP stdio server (memory_select)")

    args = parser.parse_args(argv)
    if args.command == "demo":
        return _demo()
    if args.command == "select":
        return _select(args.file, args.query, args.scope)
    if args.command == "serve":
        from .api.server import serve

        serve(Settings.from_env())
        return 0
    if args.command == "mcp":
        run_mcp(Settings.from_env())
        return 0
    parser.error("unknown command")
    return 2


def _demo() -> int:
    selector = MemorySelector(provider="mock")
    result = selector.select(
        query="english",
        memories=[
            {"id": "language", "content": "Reply in English", "scope": "demo"},
            {"id": "database", "content": "PostgreSQL database", "scope": "demo"},
        ],
        max_memories=2,
        max_tokens=8,
        scope="demo",
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


def _select(path: str, query: str | None, scope: str) -> int:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    memories = payload.get("memories") if isinstance(payload, dict) else payload
    chosen_query = query or (payload.get("query") if isinstance(payload, dict) else None)
    if not chosen_query:
        print("missing query (--query or JSON field)", file=sys.stderr)
        return 2
    settings = Settings.from_env()
    result = MemorySelector(provider=settings.provider, settings=settings).select(
        query=str(chosen_query),
        memories=memories,
        scope=scope,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
