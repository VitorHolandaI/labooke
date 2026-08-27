"""TUI pager state machine — pure logic, no terminal dependency."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PageState:
    """Immutable snapshot of the pager UI state.

    Example:
        >>> s = PageState(book_id=1, title="T", page=1, total_pages=5,
        ...               scroll=0, search_query=None, lines=[], searching=False)
        >>> s.quit
        False
    """

    book_id: int
    title: str
    page: int
    total_pages: int
    scroll: int
    search_query: str | None
    lines: list[str]
    source_text: str = ""
    quit: bool = False
    searching: bool = False
    goto_page: bool = False


def handle_key(state: PageState, key: str, viewport_rows: int = 1) -> PageState:
    """Return a new PageState reflecting one keypress.

    Left/right change pages; up/down scroll the current page.

    Example:
        >>> s = PageState(book_id=1, title="T", page=3, total_pages=5,
        ...               scroll=0, search_query=None, lines=["a"])
        >>> handle_key(s, "n").page
        4
    """
    if key in {"n", "p", "g", "G", "left", "right", "<", ">"}:
        return _move_page(state, key)
    if key in {"j", "k", " ", "f", "b", "up", "down"}:
        return _move_viewport(state, key, viewport_rows)
    if key == "q":
        return replace(state, quit=True)
    if key == "/":
        return replace(state, searching=True)
    if key == ":":
        return replace(state, goto_page=True)
    return state


def _move_page(state: PageState, key: str) -> PageState:
    targets = {
        "n": min(state.page + 1, state.total_pages),
        "p": max(state.page - 1, 1),
        "g": 1,
        "G": state.total_pages,
        "left": max(state.page - 1, 1),
        "<": max(state.page - 1, 1),
        "right": min(state.page + 1, state.total_pages),
        ">": min(state.page + 1, state.total_pages),
    }
    return replace(state, page=targets[key], scroll=0)


def _move_viewport(state: PageState, key: str, viewport_rows: int) -> PageState:
    rows = max(1, viewport_rows)
    max_scroll = max(0, len(state.lines) - rows)
    deltas = {
        "j": 1,
        "down": 1,
        "k": -1,
        "up": -1,
        " ": rows,
        "f": rows,
        "b": -rows,
    }
    scroll = max(0, min(state.scroll + deltas[key], max_scroll))
    return replace(state, scroll=scroll)


def jump_to_page(state: PageState, target: int) -> PageState:
    """Navigate to *target* page (clamped to valid range) and exit goto mode.

    Example:
        >>> s = PageState(book_id=1, title="T", page=1, total_pages=10,
        ...               scroll=2, search_query=None, lines=[], goto_page=True)
        >>> jump_to_page(s, 7).page
        7
        >>> jump_to_page(s, 99).page
        10
        >>> jump_to_page(s, 0).page
        1
    """
    page = max(1, min(target, state.total_pages))
    return replace(state, page=page, scroll=0, goto_page=False)


def set_search_query(state: PageState, query: str, viewport_rows: int = 1) -> PageState:
    """Commit a search query and exit search-input mode.

    Called by the TUI layer after the user finishes typing a / query.

    Example:
        >>> s = PageState(book_id=1, title="T", page=1, total_pages=1,
        ...               scroll=0, search_query=None, lines=[], searching=True)
        >>> set_search_query(s, "kernel").search_query
        'kernel'
    """
    normalized_query = query.casefold().strip()
    matching_line = next(
        (index for index, line in enumerate(state.lines) if normalized_query in line.casefold()),
        state.scroll,
    )
    max_scroll = max(0, len(state.lines) - max(1, viewport_rows))
    return replace(
        state,
        search_query=query,
        searching=False,
        scroll=min(matching_line, max_scroll) if normalized_query else state.scroll,
    )
