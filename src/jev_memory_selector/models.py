"""Modèles de données du sélecteur de mémoire."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"{field_name} doit être timezone-aware")
        return value
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError(f"{field_name} doit être timezone-aware")
        return parsed
    raise ValueError(f"{field_name} a un type invalide")


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
    similarity : score de retrieval optionnel, 0.0 à 1.0.
    metadata : paires libres fournies par l'appelant.
    """

    id: str
    text: str
    created_at: datetime = field(default_factory=utcnow)
    importance: float = 0.5
    tags: tuple[str, ...] = ()
    scope: str = "default"
    expires_at: datetime | None = None
    similarity: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

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
        if self.similarity is not None and not 0.0 <= self.similarity <= 1.0:
            raise ValueError("similarity doit être compris entre 0.0 et 1.0")

    def with_text(self, text: str) -> MemoryItem:
        """Copie figée avec un nouveau texte (redaction)."""
        return MemoryItem(
            id=self.id,
            text=text,
            created_at=self.created_at,
            importance=self.importance,
            tags=self.tags,
            scope=self.scope,
            expires_at=self.expires_at,
            similarity=self.similarity,
            metadata=self.metadata,
        )

    @classmethod
    def from_mapping(cls, data: MemoryItem | Mapping[str, Any]) -> MemoryItem:
        """Accepte MemoryItem ou un dict (content/text, namespace/scope)."""
        if isinstance(data, cls):
            return data
        text = data.get("text")
        if text is None:
            text = data.get("content")
        if not isinstance(text, str):
            raise ValueError("text ou content est obligatoire")
        scope = data.get("scope")
        if not scope:
            scope = data.get("namespace") or "default"
        tags = data.get("tags") or ()
        if isinstance(tags, str):
            tags = (tags,)
        created_at = _parse_datetime(data.get("created_at"), "created_at") or utcnow()
        expires_at = _parse_datetime(data.get("expires_at"), "expires_at")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("metadata doit être un objet")
        return cls(
            id=str(data.get("id") or ""),
            text=text,
            created_at=created_at,
            importance=float(data.get("importance", 0.5)),
            tags=tuple(str(tag) for tag in tags),
            scope=str(scope),
            expires_at=expires_at,
            similarity=None if data.get("similarity") is None else float(data["similarity"]),
            metadata=metadata,
        )


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

    def to_dict(self, *, include_dropped: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "selected": [
                {
                    "id": item.id,
                    "content": item.text,
                    "score": item.score,
                    "tokens": item.tokens,
                    "reasons": list(item.reasons),
                }
                for item in self.selected
            ],
            "total_tokens": self.total_tokens,
        }
        if include_dropped:
            payload["dropped"] = [
                {"id": item.id, "reason": item.reason} for item in self.dropped
            ]
        return payload
