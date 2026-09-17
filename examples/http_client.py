"""Client HTTP local. Aucune clé dans le corps."""
from __future__ import annotations

import json
import urllib.error
import urllib.request


def main() -> None:
    payload = {
        "query": "français",
        "memories": [
            {"id": "language", "content": "Répondre en français", "scope": "demo"},
            {"id": "database", "content": "Base PostgreSQL", "scope": "demo"},
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
        raise SystemExit(
            "Serveur injoignable. Lance `jev-memory serve` puis réessaie."
        ) from exc


if __name__ == "__main__":
    main()
