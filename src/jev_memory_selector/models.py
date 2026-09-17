"""Modèles de données du sélecteur de mémoire."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryItem:
    """Un élément de mémoire candidat.

    id : identifiant stable et unique.
    text : contenu envoyé au modèle si l'élément est retenu.
    created_at : date de création, obligatoirement tz-aware.
    importance : 0.0 à 1.0, fourni par l'appelant.
    tags : jetons additionnels pris en compte dans la pertinence.
    scope : isolatif, par exemple un identifiant d'utilisateur.
    expires_at : au-delà de cette date, l'élément est rejeté.
    """

    id: str
    text: str
    created_at: datetime = field(default_factory=utcnow)
    importance: float = 0.5
    tags: tuple[str, ...] = ()
    scope: str = "default"
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id est obligatoire")
        if not self.text:
            raise ValueError("text est obligatoire")
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance doit être compris entre 0.0 et 1.0")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at doit être timezone-aware")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("expires_at doit être timezone-aware")


@dataclass(frozen=True)
class SelectionRequest:
    """Une demande de sélection.

    now est injectable pour un comportement reproductible ; par défaut
    l'horloge système est utilisée.
    """

    query: str = ""
    scope: str = "default"
    budget_tokens: int = 512
    max_items: int = 15
    now: datetime | None = None

    def __post_init__(self) -> None:
        if self.budget_tokens < 1:
            raise ValueError("budget_tokens doit être >= 1")
        if self.max_items < 1:
            raise ValueError("max_items doit être >= 1")


@dataclass(frozen=True)
class SelectedMemory:
    """Un élément retenu, avec score, coût et justification."""

    id: str
    text: str
    score: float
    tokens: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DroppedMemory:
    """Un élément écarté, avec la cause du rejet."""

    id: str
    reason: str


@dataclass(frozen=True)
class SelectionResult:
    """Le résultat d'une sélection."""

    selected: tuple[SelectedMemory, ...]
    dropped: tuple[DroppedMemory, ...]
    total_tokens: int

    @property
    def texts(self) -> tuple[str, ...]:
        return tuple(item.text for item in self.selected)
