"""Normalisation des scores distants.

Un score hors [0, 1] est *rejeté*, pas borné. Un juge qui répond 1.7 ne répond pas à la
question 0-1 qui lui a été posée : la borner inventerait une confiance qui n'existe pas, et
une mémoire écrasée à 1.0 passe pour pertinente alors que le juge a surtout mal répondu.
Le caller retombe sur son score heuristique, ce qui est le comportement sûr.
"""
from __future__ import annotations

from typing import Any

from ..errors import ProviderError

def _rows(data: Any) -> list[Any] | None:
    """Normalise the envelope into a list of rows.

    Accepts a list, or a dict holding one under a known key. A dict of dicts keyed by id
    (the shape TypeSafe System One uses for ``answers``) becomes a list of rows. Any other
    dict is rejected rather than half-parsed.
    """
    if isinstance(data, dict):
        for key in ("scores", "selected", "memories", "answers", "results"):
            if key in data:
                data = data[key]
                break
        else:
            return None
    if isinstance(data, dict):
        # System One: {answers: {qid: {noul: 0.9, confidence: 0.8}}}
        return [{"id": qid, **answer} for qid, answer in data.items() if isinstance(answer, dict)]
    return data if isinstance(data, list) else None


def parse_score_list(payload: Any) -> dict[str, float]:
    """Accepte une liste, ou un objet {answers|scores|selected|memories}."""
    rows = _rows(payload)
    if rows is None:
        raise ProviderError("invalid score response")
    scores: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict) or "id" not in row:
            continue
        raw = row.get("noul", row.get("score", row.get("confidence")))
        if isinstance(raw, bool):
            continue
        try:
            score = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if not 0.0 <= score <= 1.0:
            continue
        scores[str(row["id"])] = score
    return scores
