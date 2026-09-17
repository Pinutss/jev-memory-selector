"""Démonstration locale sur données fictives, sans réseau."""
from datetime import datetime, timezone

from jev_memory_selector import MemoryItem, MemorySelector

now = datetime(2026, 9, 17, tzinfo=timezone.utc)
result = MemorySelector(provider="local").select(
    query="français",
    memories=[
        MemoryItem(id="language", text="Répondre en français", scope="demo", created_at=now),
        MemoryItem(id="database", text="Base PostgreSQL", scope="demo", created_at=now),
    ],
    max_memories=2,
    max_tokens=8,
    scope="demo",
    now=now,
)
for item in result.selected:
    print(item.id, item.tokens, item.reasons)
print("Total estimé :", result.total_tokens)
for item in result.dropped:
    print("Rejet :", item.id, item.reason)
assert [item.id for item in result.selected] == ["language"]
assert result.total_tokens <= 8
