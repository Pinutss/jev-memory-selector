"""Provider local : heuristique déterministe, hors réseau."""
from __future__ import annotations

from ..models import MemoryItem, SelectionRequest, SelectionResult
from ..selector import HeuristicSelector


class LocalProvider:
    def __init__(self, selector: HeuristicSelector | None = None) -> None:
        self._selector = selector or HeuristicSelector()

    def select(self, items: list[MemoryItem], request: SelectionRequest) -> SelectionResult:
        return self._selector.select(items, request)
