from datetime import datetime, timezone
import pytest
from jev_memory_selector import HeuristicSelector, MemoryItem, SelectionRequest


def test_default_clock():
    result = HeuristicSelector().select([MemoryItem(id="one", text="bonjour")], SelectionRequest())
    assert len(result.selected) == 1


def test_distinct_numbers_are_not_duplicates():
    items = [MemoryItem(id=str(i), text=f"facture numero {i}") for i in range(3)]
    result = HeuristicSelector().select(items, SelectionRequest())
    assert len(result.selected) == 3


@pytest.mark.parametrize("value", [-1, 0, 1.5, True])
def test_invalid_counter_fails_closed(value):
    with pytest.raises(ValueError):
        HeuristicSelector(token_counter=lambda text: value).select(
            [MemoryItem(id="one", text="bonjour")], SelectionRequest())
