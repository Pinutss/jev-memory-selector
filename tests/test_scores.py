"""Un score hors [0, 1] doit être ignoré, pas borné.

Ces tests pinning le comportement: borner un score hors range fait passer une mémoire pour
pertinente à 1.0 alors que le juge a mal répondu. Le caller doit retomber sur son score
heuristique, donc la ligne disparaît de `scores` au lieu d'être écrasée.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jev_memory_selector.errors import ProviderError  # noqa: E402
from jev_memory_selector.providers.scores import parse_score_list  # noqa: E402


def test_out_of_range_score_is_dropped_not_clamped() -> None:
    scores = parse_score_list(
        [{"id": "a", "noul": 1.7}, {"id": "b", "noul": 0.4}, {"id": "c", "noul": -0.2}]
    )
    assert scores == {"b": 0.4}, scores


def test_confidence_only_row_still_parses() -> None:
    """Backward compat: a judge that answers `score` or `confidence` still works."""
    scores = parse_score_list([{"id": "a", "score": 0.9}, {"id": "b", "confidence": 0.1}])
    assert scores == {"a": 0.9, "b": 0.1}, scores


def test_boundary_values_are_kept() -> None:
    assert parse_score_list([{"id": "a", "noul": 0.0}, {"id": "b", "noul": 1.0}]) == {
        "a": 0.0,
        "b": 1.0,
    }


def test_noul_preferred_over_score() -> None:
    """`noul` is the keep-probability; a stale `score` must not win."""
    assert parse_score_list([{"id": "a", "noul": 0.2, "score": 0.9}]) == {"a": 0.2}


def test_missing_noul_is_not_zero() -> None:
    """A row with no usable value is skipped, not scored 0.0."""
    assert parse_score_list([{"id": "a"}, {"id": "b", "noul": None}]) == {}


def test_bool_is_not_a_score() -> None:
    assert parse_score_list([{"id": "a", "noul": True}, {"id": "b", "noul": 0.5}]) == {"b": 0.5}


def test_non_list_payload_raises() -> None:
    try:
        parse_score_list({"unexpected": "shape"})
    except ProviderError:
        return
    raise AssertionError("expected ProviderError")


def test_systemone_answers_mapping_is_parsed() -> None:
    """System One's answer shape: {answers: {qid: {type, noul}}}, a dict of dicts."""
    payload = {
        "answers": {
            "m1": {"type": "noul", "noul": 0.92},
            "m2": {"type": "noul", "noul": 0.11},
        }
    }
    assert parse_score_list(payload) == {"m1": 0.92, "m2": 0.11}


def test_systemone_out_of_range_still_dropped() -> None:
    payload = {"answers": {"m1": {"noul": 1.7}, "m2": {"noul": 0.3}}}
    assert parse_score_list(payload) == {"m2": 0.3}


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("all passed")
