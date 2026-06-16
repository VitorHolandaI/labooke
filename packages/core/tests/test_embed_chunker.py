from labooke_core.domain.models import PageText
from labooke_core.embed import chunk_pages


def test_chunk_pages_groups_by_explicit_size():
    pages = [
        PageText(page_no=1, text="one"),
        PageText(page_no=2, text="two"),
        PageText(page_no=3, text="three"),
    ]
    chunks = chunk_pages(pages, pages_per_chunk=2)
    assert [(chunk.page_start, chunk.page_end) for chunk in chunks] == [(1, 2), (3, 3)]
    assert chunks[0].text == "one\n\ntwo"


def test_chunk_pages_uses_settings_when_size_omitted(monkeypatch):
    monkeypatch.setenv("LABOOKE_CHUNK_PAGES", "2")
    pages = [
        PageText(page_no=1, text="one"),
        PageText(page_no=2, text="two"),
        PageText(page_no=3, text="three"),
    ]
    chunks = chunk_pages(pages)
    assert [(chunk.page_start, chunk.page_end) for chunk in chunks] == [(1, 2), (3, 3)]


def test_chunk_pages_rejects_zero():
    try:
        chunk_pages([], pages_per_chunk=0)
        raised = False
    except ValueError as exc:
        raised = True
        assert str(exc) == "pages_per_chunk must be >= 1, got 0"
    assert raised


def test_chunk_pages_empty_input_returns_empty_list():
    assert chunk_pages([], pages_per_chunk=2) == []
