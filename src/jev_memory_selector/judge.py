"""Point d'extension pour un juge externe (JEV).

L'adaptateur JEV sera écrit lorsque la référence officielle de JEV
(contrat d'API, licence, limites de fonctionnement) sera confirmée.
En attendant, HeuristicSelector est la seule implémentation fournie.
"""
from __future__ import annotations

from typing import Protocol, Sequence

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
