"""Local HTTP client. No keys in the body."""
from __future__ import annotations

import json
import urllib.error
import urllib.request


def main() -> None:
    payload = {
        "query": "english",
        "memories": [
            {"id": "language", "content": "Reply in English", "scope": "demo"},
            {"id": "database", "content": "PostgreSQL database", "scope": "demo"},
        ],
        "max_memories": 2,
        "max_tokens": 32,
        "scope": "demo",
    }
    request = urllib.request.Request(
        "http://127.0.0.1:8080/v1/select",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit("Server unreachable. Run `jev-memory serve` and try again.") from exc


if __name__ == "__main__":
    main()
