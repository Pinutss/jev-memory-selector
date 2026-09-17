from datetime import datetime, timezone

import pytest

from jev_memory_selector import MemoryItem


def test_content_and_namespace_aliases():
    item = MemoryItem.from_mapping(
        {
            "id": "1",
            "content": "Backend FastAPI",
            "namespace": "proj",
            "similarity": 0.91,
            "metadata": {"source": "note"},
        }
    )
    assert item.text == "Backend FastAPI"
    assert item.scope == "proj"
    assert item.similarity == 0.91
    assert item.metadata["source"] == "note"


def test_from_mapping_accepts_item():
    item = MemoryItem(id="a", text="hello")
    assert MemoryItem.from_mapping(item) is item


def test_similarity_bounds():
    with pytest.raises(ValueError):
        MemoryItem(id="a", text="hello", similarity=1.5)


def test_created_at_iso():
    item = MemoryItem.from_mapping(
        {
            "id": "a",
            "text": "hello",
            "created_at": "2026-09-17T12:00:00Z",
        }
    )
    assert item.created_at == datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)
