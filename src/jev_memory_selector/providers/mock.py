"""Provider de démonstration, déterministe, hors réseau."""
from __future__ import annotations

from ..models import MemoryItem, SelectionRequest, SelectionResult
from ..selector import HeuristicSelector


class MockProvider:
    """Classement lexical fixe, pour `jev-memory demo` et la CI."""

    def __init__(self) -> None:
        self._selector = HeuristicSelector(min_relevance=0.0)

    def select(self, items: list[MemoryItem], request: SelectionRequest) -> SelectionResult:
        return self._selector.select(items, request)
