"""Démonstration locale sur données fictives, sans réseau."""
from datetime import datetime, timezone
from jev_memory_selector import HeuristicSelector, MemoryItem, SelectionRequest

now = datetime(2026, 9, 17, tzinfo=timezone.utc)
items = [
    MemoryItem(id="language", text="Répondre en français", scope="demo", created_at=now),
    MemoryItem(id="database", text="Base PostgreSQL", scope="demo", created_at=now),
]
result = HeuristicSelector().select(items, SelectionRequest(
    query="français", scope="demo", budget_tokens=8, now=now))
for item in result.selected:
    print(item.id, item.tokens, item.reasons)
print("Total estimé :", result.total_tokens)
for item in result.dropped:
    print("Rejet :", item.id, item.reason)
assert [item.id for item in result.selected] == ["language"]
assert result.total_tokens <= 8
