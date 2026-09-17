"""Interface commune des providers."""
from __future__ import annotations

from typing import Protocol

from ..models import MemoryItem, SelectionRequest, SelectionResult


class DecisionProvider(Protocol):
    def select(
        self,
        items: list[MemoryItem],
        request: SelectionRequest,
    ) -> SelectionResult:
        """Retourne une sélection sous budget."""
        ...
