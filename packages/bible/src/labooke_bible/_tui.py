"""prompt_toolkit TUI for paging through book pages."""

from __future__ import annotations

import textwrap
from collections.abc import Callable

from labooke_bible._pager import PageState, handle_key, jump_to_page

GetPageText = Callable[[int, int], str]  # (book_id, page_no) -> text


def _load_page(
    get_page_text: GetPageText, state: PageState, *, width: int
) -> PageState:
    """Fetch page text and reflow it into wrapped lines.

    Extracted so it can be unit-tested without a live terminal.

    Example:
        >>> _load_page.__name__
        '_load_page'
    """
    text = get_page_text(state.book_id, state.page)
    lines = textwrap.wrap(text, width) or ["(empty page)"]
    return PageState(
        book_id=state.book_id,
        title=state.title,
        page=state.page,
        total_pages=state.total_pages,
        scroll=0,
        search_query=state.search_query,
        lines=lines,
    )


def run_pager(
    get_page_text: GetPageText,
    book_id: int,
    title: str,
    total_pages: int,
    start_page: int = 1,
) -> None:
    """Launch the interactive pager for *book_id* starting at *start_page*.

    Keys: j/k scroll, n/p page, g/G first/last, / search, : goto page, q quit.

    Example:
        >>> run_pager.__name__
        'run_pager'
    """
    import shutil

    from prompt_toolkit.shortcuts import clear, prompt

    width = shutil.get_terminal_size().columns
    state = _load_page(
        get_page_text,
        PageState(
            book_id=book_id,
            title=title,
            page=start_page,
            total_pages=total_pages,
            scroll=0,
            search_query=None,
            lines=[],
        ),
        width=width,
    )

    while True:
        clear()
        _render(state)
        try:
            key = _read_key()
        except (KeyboardInterrupt, EOFError):
            break
        new_state = handle_key(state, key)
        if new_state.quit:
            break
        if new_state.searching:
            query = prompt("/ ")
            from labooke_bible._pager import set_search_query

            new_state = set_search_query(new_state, query)
        if new_state.goto_page:
            raw = prompt(": ", default="")
            try:
                new_state = jump_to_page(new_state, int(raw))
            except ValueError:
                new_state = jump_to_page(new_state, state.page)
        if new_state.page != state.page:
            width = shutil.get_terminal_size().columns
            new_state = _load_page(get_page_text, new_state, width=width)
        state = new_state


def _render(state: PageState) -> None:
    """Print the current page and status bar to stdout."""
    import shutil

    width = shutil.get_terminal_size().columns
    visible = state.lines[state.scroll :]
    print("\n".join(visible))
    status = f" {state.title} — page {state.page}/{state.total_pages}  [: goto] "
    print("\n" + status.center(width, "─"))


def _read_key() -> str:
    """Read a single keypress from stdin (raw mode)."""
    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch
