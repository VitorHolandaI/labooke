"""Tests that the TUI pager loads pages lazily via a get_page_text callable."""

import os
from dataclasses import replace
from os import terminal_size

from labooke_bible._pager import PageState, handle_key
from labooke_bible._tui import (
    _frame_lines,
    _initial_state,
    _load_page,
    _navigation_key,
    _normalize_key,
    _read_escape_tail,
    _reading_width,
    _reflow_page,
    _resolve_prompt,
    _wrap_page_text,
)


class RecordingPageLoader:
    """Callable page loader that records calls for pager tests."""

    def __init__(self, text: str = "hello world") -> None:
        self.calls: list[tuple[int, int]] = []
        self._text = text

    def __call__(self, book_id: int, page_no: int) -> str:
        """Return canned text and record the requested page."""
        self.calls.append((book_id, page_no))
        return self._text


class QueuedPrompt:
    """Return predefined prompt responses in order."""

    def __init__(self, *responses: str) -> None:
        self._responses = iter(responses)

    def __call__(self, _message: str, **_kwargs: str) -> str:
        """Return the next predefined response."""
        return next(self._responses)


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


def test_initial_state_clamps_page_and_loads_it():
    get_page = _get_page_text("content")
    state = _initial_state(get_page, 1, "Test", 5, 99, 80)
    assert state.page == 5
    assert get_page.calls == [(1, 5)]


def test_reflow_page_uses_saved_source_text():
    loaded = _load_page(_get_page_text("one two three"), _base_state(), width=20)
    reflowed = _reflow_page(loaded, width=5)
    assert reflowed.lines == ["one", "two", "three"]


def test_wrap_page_text_preserves_paragraph_breaks():
    assert _wrap_page_text("first paragraph\n\nsecond paragraph", 40) == [
        "first paragraph",
        "",
        "second paragraph",
    ]


def test_reading_width_keeps_book_text_narrow():
    assert _reading_width(160) == 88
    assert _reading_width(80) == 76


def test_normalize_key_decodes_arrow_sequences():
    assert _normalize_key("\x1b[A") == "up"
    assert _normalize_key("\x1b[B") == "down"
    assert _normalize_key("\x1b[C") == "right"
    assert _normalize_key("\x1b[D") == "left"
    assert _normalize_key("\x1bOA") == "up"
    assert _normalize_key("\x1bOC") == "right"


def test_read_escape_tail_returns_without_key_repeat():
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, b"[C")
        assert _read_escape_tail(read_fd) == b"[C"
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_normalize_mouse_decodes_click_and_wheel():
    assert _normalize_key("\x1b[<0;70;8M") == "click:70"
    assert _normalize_key("\x1b[<64;10;8M") == "up"
    assert _normalize_key("\x1b[<65;10;8M") == "down"
    assert _normalize_key("\x1b[<0;70;8m") == ""


def test_navigation_key_uses_clicked_terminal_half():
    assert _navigation_key("click:20", columns=80) == "left"
    assert _navigation_key("click:60", columns=80) == "right"


def test_frame_fills_terminal_and_keeps_footer_visible():
    state = replace(_base_state(), lines=[f"line {index}" for index in range(30)])
    frame = _frame_lines(state, terminal_size((40, 10)))
    assert len(frame) == 10
    assert frame[1].strip() == "line 0"
    assert "pág. 1/5" in frame[-1]
    assert "linhas" not in frame[-1]
    assert "line 8" not in frame


def test_resolve_search_prompt_moves_to_match():
    state = replace(_base_state(), lines=["one", "needle", "three"], searching=True)
    resolved = _resolve_prompt(state, 1, 4, QueuedPrompt("needle"))
    assert resolved.search_query == "needle"
    assert resolved.scroll == 1


def test_resolve_invalid_page_prompt_keeps_current_page():
    state = replace(_base_state(page=3), goto_page=True)
    resolved = _resolve_prompt(state, 3, 10, QueuedPrompt("invalid"))
    assert resolved.page == 3
    assert resolved.goto_page is False


def test_page_change_triggers_reload():
    get_page = _get_page_text()
    state = _base_state(page=1)
    loaded = _load_page(get_page, state, width=80)
    new_state = handle_key(loaded, "n")
    _load_page(get_page, new_state, width=80)
    assert len(get_page.calls) == 2
    assert get_page.calls == [(1, 1), (1, 2)]
