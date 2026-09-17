"""Tests du sélecteur heuristique."""
from datetime import datetime, timedelta, timezone

import pytest

from jev_memory_selector import HeuristicSelector, MemoryItem, SelectionRequest

NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


def item(id="m1", text="texte", importance=0.5, created_at=None, scope="default", expires_at=None):
    return MemoryItem(
        id=id,
        text=text,
        created_at=created_at or NOW - timedelta(days=1),
        importance=importance,
        scope=scope,
        expires_at=expires_at,
    )


def test_budget_est_respecte():
    items = [item(id=f"m{i}", text=f"contenu numero {i}") for i in range(5)]
    result = HeuristicSelector().select(items, SelectionRequest(budget_tokens=12, now=NOW))
    assert result.total_tokens <= 12
    assert any(d.reason == "budget" for d in result.dropped)


def test_element_expire_rejete():
    items = [item(expires_at=NOW - timedelta(hours=1))]
    result = HeuristicSelector().select(items, SelectionRequest(now=NOW))
    assert [d.reason for d in result.dropped] == ["expired"]
    assert result.selected == ()


def test_isolation_par_scope():
    items = [item(id="a", scope="user-1", text="préférence utilisateur")]
    result = HeuristicSelector().select(items, SelectionRequest(scope="user-2", now=NOW))
    assert [d.reason for d in result.dropped] == ["out_of_scope"]
    assert result.selected == ()


def test_pertinence_classee_en_premier():
    items = [
        item(id="gen", text="note générale sur le projet"),
        item(id="spec", text="bug d'affichage Safari sur la page de paiement"),
    ]
    result = HeuristicSelector().select(items, SelectionRequest(query="bug Safari affichage", now=NOW))
    assert result.selected[0].id == "spec"
    assert any(r.startswith("relevance=") for r in result.selected[0].reasons)


def test_doublon_rejete():
    text = "déploiement sur Fly.io chaque vendredi soir"
    items = [item(id="a", text=text), item(id="b", text=text)]
    result = HeuristicSelector().select(items, SelectionRequest(now=NOW))
    assert [s.id for s in result.selected] == ["a"]
    assert any(d.reason == "duplicate_of:a" for d in result.dropped)


def test_magasin_vide():
    result = HeuristicSelector().select([], SelectionRequest(now=NOW))
    assert result.selected == ()
    assert result.total_tokens == 0


def test_determinisme_sans_egard_a_l_ordre_d_entree():
    items = [
        item(id=f"m{i}", text=f"élément numéro {i}", importance=0.2 + i / 10)
        for i in range(6)
    ]
    r1 = HeuristicSelector().select(items, SelectionRequest(now=NOW))
    r2 = HeuristicSelector().select(list(reversed(items)), SelectionRequest(now=NOW))
    assert [s.id for s in r1.selected] == [s.id for s in r2.selected]


def test_fraicheur_departage():
    recent = item(id="recent", text="préférence récente", created_at=NOW - timedelta(hours=1))
    ancien = item(id="ancien", text="préférence ancienne", created_at=NOW - timedelta(days=30))
    result = HeuristicSelector().select([ancien, recent], SelectionRequest(now=NOW))
    assert result.selected[0].id == "recent"


def test_importance_departage():
    fort = item(id="fort", text="tâche importante", importance=0.9)
    faible = item(id="faible", text="tâche secondaire", importance=0.1)
    result = HeuristicSelector().select([faible, fort], SelectionRequest(now=NOW))
    assert result.selected[0].id == "fort"


def test_max_items():
    items = [item(id=f"m{i}", text=f"contenu distinct {i}") for i in range(5)]
    result = HeuristicSelector().select(items, SelectionRequest(max_items=2, now=NOW))
    assert len(result.selected) == 2
    assert sum(1 for d in result.dropped if d.reason == "max_items") == 3


def test_importance_validee():
    with pytest.raises(ValueError):
        item(importance=1.5)
