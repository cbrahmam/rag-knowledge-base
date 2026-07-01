import pytest
from fastapi import HTTPException

from routers.documents import _safe_filename, _find_duplicate, _to_list_item


def test_safe_filename_strips_directories():
    assert _safe_filename("../../etc/passwd") == "passwd"
    assert _safe_filename("/tmp/evil.md") == "evil.md"
    assert _safe_filename("report.pdf") == "report.pdf"


@pytest.mark.parametrize("bad", ["", None, "..", ".", "/", "../"])
def test_safe_filename_rejects_invalid(bad):
    with pytest.raises(HTTPException):
        _safe_filename(bad)


def test_find_duplicate():
    store = {"a.md": {"content_hash": "x"}, "b.md": {"content_hash": "y"}}
    assert _find_duplicate(store, "x", "c.md") == "a.md"
    assert _find_duplicate(store, "z", "c.md") is None
    # A file doesn't count as a duplicate of itself.
    assert _find_duplicate(store, "x", "a.md") is None


def test_to_list_item_defaults():
    item = _to_list_item("a.md", {
        "file_type": "md", "total_chunks": 3, "uploaded_at": "t", "size_bytes": 10,
    })
    assert item.collection == "General"
    assert item.tags == []
