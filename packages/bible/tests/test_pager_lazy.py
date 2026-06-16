"""Tests that the TUI pager loads pages lazily via a get_page_text callable."""

from labooke_bible._pager import PageState, handle_key
from labooke_bible._tui import _load_page


class RecordingPageLoader:
    """Callable page loader that records calls for pager tests."""

    def __init__(self, text: str = "hello world") -> None:
        self.calls: list[tuple[int, int]] = []
        self._text = text

    def __call__(self, book_id: int, page_no: int) -> str:
        """Return canned text and record the requested page."""
        self.calls.append((book_id, page_no))
        return self._text


def _get_page_text(text: str = "hello world") -> RecordingPageLoader:
    return RecordingPageLoader(text)


def _base_state(page: int = 1, total: int = 5) -> PageState:
    return PageState(
        book_id=1,
        title="Test",
        page=page,
        total_pages=total,
        scroll=0,
        search_query=None,
        lines=[],
    )


def test_load_page_calls_reader_once():
    get_page = _get_page_text("some content")
    state = _base_state(page=2)
    loaded = _load_page(get_page, state, width=80)
    assert get_page.calls == [(1, 2)]
    assert len(loaded.lines) > 0


def test_load_page_wraps_text_to_width():
    long_text = "word " * 30
    get_page = _get_page_text(long_text)
    loaded = _load_page(get_page, _base_state(), width=40)
    assert all(len(line) <= 40 for line in loaded.lines)


def test_page_change_triggers_reload():
    get_page = _get_page_text()
    state = _base_state(page=1)
    loaded = _load_page(get_page, state, width=80)
    new_state = handle_key(loaded, "n")
    _load_page(get_page, new_state, width=80)
    assert len(get_page.calls) == 2
    assert get_page.calls == [(1, 1), (1, 2)]
