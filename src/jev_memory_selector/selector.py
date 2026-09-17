"""Sélecteur heuristique déterministe, sans dépendance à l'exécution."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from .models import (
    DroppedMemory,
    MemoryItem,
    SelectionRequest,
    SelectionResult,
    SelectedMemory,
)
from .tokens import TokenCounter, estimate_tokens

_WORD_RE = re.compile(r"[a-z0-9àâäéèêëíìîïòóôöùúûüçñ]+")
_STOPWORDS = frozenset(
    """au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma
    mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se
    ses son sur ta te tes toi ton tu un une vos votre vous c d j l à m n s t y été
    the a an and or of to in for with without is are was were be been this that
    """.split()
)


def tokenize(text: str) -> frozenset[str]:
    """Jetons minuscules, sans mots vides, pour le scoring lexical."""
    return frozenset(
        word
        for word in _WORD_RE.findall(text.lower())
        if (len(word) > 1 or word.isdigit()) and word not in _STOPWORDS
    )


@dataclass
class HeuristicSelector:
    """Sélection déterministe sous budget, sans appel réseau.

    Score = pertinence lexicale * w_relevance
          + fraîcheur (demi-vie configurable) * w_recency
          + importance * w_importance

    Les égalités sont départagées par date décroissante puis identifiant
    croissant : deux exécutions sur les mêmes données donnent le même
    résultat. Un élément hors scope n'est jamais retenu, quel que soit
    son score.
    """

    w_relevance: float = 0.5
    w_recency: float = 0.3
    w_importance: float = 0.2
    recency_halflife_days: float = 14.0
    dedup_threshold: float = 0.8
    token_counter: TokenCounter = estimate_tokens

    def __post_init__(self) -> None:
        if self.recency_halflife_days <= 0:
            raise ValueError("recency_halflife_days doit être > 0")
        if not 0.0 < self.dedup_threshold <= 1.0:
            raise ValueError("dedup_threshold doit être dans (0.0, 1.0]")

    def select(self, items: list[MemoryItem], request: SelectionRequest) -> SelectionResult:
        now = request.now or datetime.now().astimezone()
        if now.tzinfo is None:
            raise ValueError("SelectionRequest.now doit être timezone-aware")

        dropped: list[DroppedMemory] = []
        seen: set[str] = set()
        candidates: list[tuple[float, float, float, MemoryItem]] = []

        for item in items:
            if item.id in seen:
                dropped.append(DroppedMemory(item.id, "duplicate_input"))
                continue
            seen.add(item.id)
            if item.scope != request.scope:
                dropped.append(DroppedMemory(item.id, "out_of_scope"))
                continue
            if item.expires_at is not None and item.expires_at <= now:
                dropped.append(DroppedMemory(item.id, "expired"))
                continue

            query_tokens = tokenize(request.query)
            item_tokens = tokenize(item.text) | set(item.tags)
            relevance = (
                len(query_tokens & item_tokens) / len(query_tokens) if query_tokens else 0.0
            )
            age_days = max(0.0, (now - item.created_at).total_seconds() / 86400)
            recency = 0.5 ** (age_days / self.recency_halflife_days)
            score = (
                self.w_relevance * relevance
                + self.w_recency * recency
                + self.w_importance * item.importance
            )
            candidates.append((score, relevance, recency, item))

        candidates.sort(
            key=lambda c: (-round(c[0], 6), -c[3].created_at.timestamp(), c[3].id)
        )

        selected: list[SelectedMemory] = []
        selected_tokens: list[frozenset[str]] = []
        total = 0

        for score, relevance, recency, item in candidates:
            if len(selected) >= request.max_items:
                dropped.append(DroppedMemory(item.id, "max_items"))
                continue
            tokens = self.token_counter(item.text)
            if type(tokens) is not int or tokens < 1:
                raise ValueError("token_counter doit retourner un entier strictement positif")
            if total + tokens > request.budget_tokens:
                dropped.append(DroppedMemory(item.id, "budget"))
                continue

            item_tokens = tokenize(item.text)
            duplicate_of = None
            for kept_id, kept_tokens in zip((s.id for s in selected), selected_tokens):
                union = len(item_tokens | kept_tokens)
                if union and len(item_tokens & kept_tokens) / union >= self.dedup_threshold:
                    duplicate_of = kept_id
                    break
            if duplicate_of is not None:
                dropped.append(DroppedMemory(item.id, f"duplicate_of:{duplicate_of}"))
                continue

            selected.append(
                SelectedMemory(
                    id=item.id,
                    text=item.text,
                    score=round(score, 6),
                    tokens=tokens,
                    reasons=(
                        f"relevance={relevance:.2f}",
                        f"recency={recency:.2f}",
                        f"importance={item.importance:.2f}",
                    ),
                )
            )
            selected_tokens.append(item_tokens)
            total += tokens

        return SelectionResult(
            selected=tuple(selected), dropped=tuple(dropped), total_tokens=total
        )
