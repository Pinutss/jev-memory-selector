"""Point d'extension interne pour un juge externe.

Ce protocole n'est pas exporté. HeuristicSelector et les providers
JEV / gateway couvrent le classement public.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from .models import MemoryItem, SelectionRequest


class Judge(Protocol):
    """Réordonne des candidats déjà filtrés et valides.

    Contrat attendu : sortie déterministe pour une entrée donnée, aucun
    effet de bord, aucune élévation de permissions. Un juge ne peut pas
    réintroduire un élément rejeté par les règles d'accès.
    """

    def rerank(
        self,
        request: SelectionRequest,
        candidates: Sequence[MemoryItem],
    ) -> Sequence[tuple[MemoryItem, float, tuple[str, ...]]]:
        """Retourne les candidats ordonnés, avec score et justification."""
        ...
