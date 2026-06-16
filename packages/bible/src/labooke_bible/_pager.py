"""TUI pager state machine — pure logic, no terminal dependency."""

from __future__ import annotations

from dataclasses import dataclass


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
    quit: bool = False
    searching: bool = False
    goto_page: bool = False


def handle_key(state: PageState, key: str) -> PageState:
    """Return a new PageState reflecting one keypress.

    Recognised keys: j k n p g G q / :. Unknown keys are ignored.

    Example:
        >>> s = PageState(book_id=1, title="T", page=3, total_pages=5,
        ...               scroll=0, search_query=None, lines=["a"])
        >>> handle_key(s, "n").page
        4
    """
    if key == "n":
        return _replace(state, page=min(state.page + 1, state.total_pages), scroll=0)
    if key == "p":
        return _replace(state, page=max(state.page - 1, 1), scroll=0)
    if key == "g":
        return _replace(state, page=1, scroll=0)
    if key == "G":
        return _replace(state, page=state.total_pages, scroll=0)
    if key == "j":
        max_scroll = max(0, len(state.lines) - 1)
        return _replace(state, scroll=min(state.scroll + 1, max_scroll))
    if key == "k":
        return _replace(state, scroll=max(state.scroll - 1, 0))
    if key == "q":
        return _replace(state, quit=True)
    if key == "/":
        return _replace(state, searching=True)
    if key == ":":
        return _replace(state, goto_page=True)
    return state


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
    return _replace(state, page=page, scroll=0, goto_page=False)


def set_search_query(state: PageState, query: str) -> PageState:
    """Commit a search query and exit search-input mode.

    Called by the TUI layer after the user finishes typing a / query.

    Example:
        >>> s = PageState(book_id=1, title="T", page=1, total_pages=1,
        ...               scroll=0, search_query=None, lines=[], searching=True)
        >>> set_search_query(s, "kernel").search_query
        'kernel'
    """
    return _replace(state, search_query=query, searching=False)


def _replace(state: PageState, **changes: object) -> PageState:
    return PageState(
        book_id=changes.get("book_id", state.book_id),  # type: ignore[arg-type]
        title=changes.get("title", state.title),  # type: ignore[arg-type]
        page=changes.get("page", state.page),  # type: ignore[arg-type]
        total_pages=changes.get("total_pages", state.total_pages),  # type: ignore[arg-type]
        scroll=changes.get("scroll", state.scroll),  # type: ignore[arg-type]
        search_query=changes.get("search_query", state.search_query),  # type: ignore[arg-type]
        lines=changes.get("lines", state.lines),  # type: ignore[arg-type]
        quit=changes.get("quit", state.quit),  # type: ignore[arg-type]
        searching=changes.get("searching", state.searching),  # type: ignore[arg-type]
        goto_page=changes.get("goto_page", state.goto_page),  # type: ignore[arg-type]
    )
