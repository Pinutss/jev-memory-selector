"""Sélecteur heuristique déterministe, sans dépendance à l'exécution."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .models import (
    DroppedMemory,
    MemoryItem,
    SelectedMemory,
    SelectionRequest,
    SelectionResult,
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
_CONTRADICTIONS: tuple[tuple[frozenset[str], frozenset[str]], ...] = (
    (frozenset({"mysql"}), frozenset({"postgresql", "postgres"})),
    (frozenset({"sqlite"}), frozenset({"postgresql", "postgres", "mysql"})),
)

Candidate = tuple[float, float, float, MemoryItem]


def tokenize(text: str) -> frozenset[str]:
    """Jetons minuscules, sans mots vides, pour le scoring lexical."""
    return frozenset(
        word
        for word in _WORD_RE.findall(text.lower())
        if (len(word) > 1 or word.isdigit()) and word not in _STOPWORDS
    )


def item_tokens(item: MemoryItem) -> frozenset[str]:
    tokens = set(tokenize(item.text))
    for tag in item.tags:
        tokens.update(tokenize(tag))
    return frozenset(tokens)


def _contradiction_with(item: MemoryItem, selected: list[SelectedMemory]) -> str | None:
    left = tokenize(item.text)
    for kept in selected:
        right = tokenize(kept.text)
        for a, b in _CONTRADICTIONS:
            if (left & a and right & b) or (left & b and right & a):
                return kept.id
    return None


@dataclass
class HeuristicSelector:
    """Sélection déterministe sous budget, sans appel réseau.

    Score = pertinence lexicale * w_relevance
          + fraîcheur (demi-vie configurable) * w_recency
          + importance * w_importance
          + similarity * w_similarity
          + score JEV * w_jev
          + score gateway * w_gateway

    Les égalités sont départagées par date décroissante puis identifiant
    croissant : deux exécutions sur les mêmes données donnent le même
    résultat. Un élément hors scope n'est jamais retenu, quel que soit
    son score.
    """

    w_relevance: float = 0.5
    w_recency: float = 0.3
    w_importance: float = 0.2
    w_similarity: float = 0.0
    w_jev: float = 0.0
    w_gateway: float = 0.0
    recency_halflife_days: float = 14.0
    dedup_threshold: float = 0.8
    min_relevance: float = 0.0
    token_counter: TokenCounter = estimate_tokens

    def __post_init__(self) -> None:
        if self.recency_halflife_days <= 0:
            raise ValueError("recency_halflife_days doit être > 0")
        if not 0.0 < self.dedup_threshold <= 1.0:
            raise ValueError("dedup_threshold doit être dans (0.0, 1.0]")
        if not 0.0 <= self.min_relevance <= 1.0:
            raise ValueError("min_relevance doit être compris entre 0.0 et 1.0")

    def collect(
        self,
        items: list[MemoryItem],
        request: SelectionRequest,
        jev_scores: Mapping[str, float] | None = None,
        gateway_scores: Mapping[str, float] | None = None,
    ) -> tuple[list[Candidate], list[DroppedMemory]]:
        now = request.now or datetime.now().astimezone()
        if now.tzinfo is None:
            raise ValueError("SelectionRequest.now doit être timezone-aware")

        jev_scores = jev_scores or {}
        gateway_scores = gateway_scores or {}
        query_tokens = tokenize(request.query)
        dropped: list[DroppedMemory] = []
        seen: set[str] = set()
        candidates: list[Candidate] = []

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

            tokens = item_tokens(item)
            relevance = (
                len(query_tokens & tokens) / len(query_tokens) if query_tokens else 0.0
            )
            jev_score = float(jev_scores.get(item.id, 0.0))
            gateway_score = float(gateway_scores.get(item.id, 0.0))
            similarity = item.similarity or 0.0
            threshold_signal = max(relevance, jev_score, gateway_score, similarity)
            if query_tokens and threshold_signal < self.min_relevance:
                dropped.append(DroppedMemory(item.id, "low_relevance"))
                continue

            age_days = max(0.0, (now - item.created_at).total_seconds() / 86400)
            recency = 0.5 ** (age_days / self.recency_halflife_days)
            score = (
                self.w_relevance * relevance
                + self.w_recency * recency
                + self.w_importance * item.importance
                + self.w_similarity * similarity
                + self.w_jev * jev_score
                + self.w_gateway * gateway_score
            )
            candidates.append((score, relevance, recency, item))

        candidates.sort(
            key=lambda c: (-round(c[0], 6), -c[3].created_at.timestamp(), c[3].id)
        )
        return candidates, dropped

    def select(
        self,
        items: list[MemoryItem],
        request: SelectionRequest,
        jev_scores: Mapping[str, float] | None = None,
        gateway_scores: Mapping[str, float] | None = None,
    ) -> SelectionResult:
        candidates, dropped = self.collect(
            items, request, jev_scores=jev_scores, gateway_scores=gateway_scores
        )
        return self.apply_budget(
            candidates, dropped, request, jev_scores=jev_scores, gateway_scores=gateway_scores
        )

    def apply_budget(
        self,
        candidates: list[Candidate],
        dropped: list[DroppedMemory],
        request: SelectionRequest,
        jev_scores: Mapping[str, float] | None = None,
        gateway_scores: Mapping[str, float] | None = None,
    ) -> SelectionResult:
        jev_scores = jev_scores or {}
        gateway_scores = gateway_scores or {}
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

            text_tokens = tokenize(item.text)
            duplicate_of = None
            for kept_id, kept_tokens in zip((s.id for s in selected), selected_tokens):
                union = len(text_tokens | kept_tokens)
                if union and len(text_tokens & kept_tokens) / union >= self.dedup_threshold:
                    duplicate_of = kept_id
                    break
            if duplicate_of is not None:
                dropped.append(DroppedMemory(item.id, f"duplicate_of:{duplicate_of}"))
                continue

            reasons = [
                f"relevance={relevance:.2f}",
                f"recency={recency:.2f}",
                f"importance={item.importance:.2f}",
            ]
            if item.similarity is not None:
                reasons.append(f"similarity={item.similarity:.2f}")
            if item.id in jev_scores:
                reasons.append(f"jev={float(jev_scores[item.id]):.2f}")
            if item.id in gateway_scores:
                reasons.append(f"gateway={float(gateway_scores[item.id]):.2f}")
            conflict = _contradiction_with(item, selected)
            if conflict is not None:
                reasons.append(f"possible_conflict:{conflict}")

            selected.append(
                SelectedMemory(
                    id=item.id,
                    text=item.text,
                    score=round(score, 6),
                    tokens=tokens,
                    reasons=tuple(reasons),
                )
            )
            selected_tokens.append(text_tokens)
            total += tokens

        return SelectionResult(
            selected=tuple(selected), dropped=tuple(dropped), total_tokens=total
        )
