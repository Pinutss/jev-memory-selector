import json

from jev_memory_selector.cli import main


def test_demo_exits_zero(capsys):
    assert main(["demo"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["selected"][0]["id"] == "language"
