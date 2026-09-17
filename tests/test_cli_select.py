import json

from jev_memory_selector.cli import main


def test_select_from_file(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("JEV_PROVIDER", "local")
    path = tmp_path / "memories.json"
    path.write_text(
        json.dumps(
            {
                "query": "français",
                "memories": [{"id": "m1", "content": "Répondre en français"}],
            }
        ),
        encoding="utf-8",
    )
    assert main(["select", "--file", str(path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"][0]["id"] == "m1"
