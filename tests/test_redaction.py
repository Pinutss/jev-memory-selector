from jev_memory_selector import MemoryItem, redact_text
from jev_memory_selector.security.redaction import redact_item


def test_redacts_common_secrets():
    text = "key sk-abcdefghijklmnopqrstuvwxyz123456 and jev_abcdefgh token Bearer abc.def"
    out = redact_text(text)
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in out
    assert "jev_abcdefgh" not in out
    assert "Bearer abc.def" not in out
    assert "[REDACTED_API_KEY]" in out


def test_redact_item_keeps_id():
    item = MemoryItem(id="m1", text="secret sk-ant-abcdefghijklmnopqrstuvwxyz")
    redacted = redact_item(item)
    assert redacted.id == "m1"
    assert "sk-ant-" not in redacted.text
