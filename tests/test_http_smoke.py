import json
import threading
from urllib.request import Request, urlopen

from jev_memory_selector.api.server import create_server
from jev_memory_selector.config import Settings


def test_healthz_and_select_over_http():
    settings = Settings(
        provider="local",
        host="127.0.0.1",
        port=0,
        redact_secrets=False,
        min_relevance=0.0,
    )
    server = create_server(settings)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        with urlopen(f"http://{host}:{port}/healthz", timeout=5) as response:
            assert json.loads(response.read().decode())["ok"] is True
        with urlopen(f"http://{host}:{port}/", timeout=5) as response:
            html = response.read().decode()
        assert "Lancer la sélection" in html
        payload = {
            "query": "français",
            "memories": [{"id": "m1", "content": "Répondre en français"}],
            "max_tokens": 32,
        }
        request = Request(
            f"http://{host}:{port}/v1/select",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode())
        assert body["selected"][0]["id"] == "m1"
    finally:
        server.shutdown()
        server.server_close()
