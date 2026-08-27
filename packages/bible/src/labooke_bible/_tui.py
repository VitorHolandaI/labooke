"""prompt_toolkit TUI for paging through book pages."""

from __future__ import annotations

import os
import select
import textwrap
from collections.abc import Callable
from dataclasses import replace
from os import terminal_size

from labooke_bible._pager import PageState, handle_key, jump_to_page, set_search_query

GetPageText = Callable[[int, int], str]  # (book_id, page_no) -> text
PromptInput = Callable[..., str]
MAX_READING_WIDTH = 88
FRAME_ROWS = 2
ARROW_SEQUENCES = {
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
    "\x1bOA": "up",
    "\x1bOB": "down",
    "\x1bOC": "right",
    "\x1bOD": "left",
}
ENABLE_MOUSE_TRACKING = "\x1b[?1000h\x1b[?1006h"
DISABLE_MOUSE_TRACKING = "\x1b[?1000l\x1b[?1006l"


def _reading_width(columns: int) -> int:
    return max(1, min(MAX_READING_WIDTH, columns - 4 if columns > 8 else columns))


def _wrap_page_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for source_line in text.splitlines():
        lines.extend(textwrap.wrap(source_line, width=width) or [""])
    return lines or ["(empty page)"]


def _load_page(get_page_text: GetPageText, state: PageState, *, width: int) -> PageState:
    """Fetch page text and reflow it into wrapped lines.

    Extracted so it can be unit-tested without a live terminal.

    Example:
        >>> _load_page.__name__
        '_load_page'
    """
    text = get_page_text(state.book_id, state.page)
    return replace(
        state,
        scroll=0,
        lines=_wrap_page_text(text, width),
        source_text=text,
        searching=False,
        goto_page=False,
    )


def _reflow_page(state: PageState, width: int) -> PageState:
    return replace(state, scroll=0, lines=_wrap_page_text(state.source_text, width))


def run_pager(
    get_page_text: GetPageText,
    book_id: int,
    title: str,
    total_pages: int,
    start_page: int = 1,
) -> None:
    """Launch the interactive pager for *book_id* starting at *start_page*.

    Keys: left/right change pages; up/down scroll; /, : and q control the reader.

    Example:
        >>> run_pager.__name__
        'run_pager'
    """
    import shutil

    from prompt_toolkit.shortcuts import clear, prompt

    size = shutil.get_terminal_size(fallback=(80, 24))
    width = _reading_width(size.columns)
    state = _initial_state(get_page_text, book_id, title, total_pages, start_page, width)
    _set_mouse_tracking(True)
    try:
        _pager_loop(get_page_text, state, width, clear, prompt)
    finally:
        _set_mouse_tracking(False)
        print()


def _initial_state(
    get_page_text: GetPageText,
    book_id: int,
    title: str,
    total_pages: int,
    start_page: int,
    width: int,
) -> PageState:
    page = max(1, min(start_page, total_pages))
    state = PageState(book_id, title, page, total_pages, 0, None, [])
    return _load_page(get_page_text, state, width=width)


def _pager_loop(
    get_page_text: GetPageText,
    state: PageState,
    width: int,
    clear_screen: Callable[[], None],
    prompt_input: PromptInput,
) -> None:
    import shutil

    while True:
        size = shutil.get_terminal_size(fallback=(80, 24))
        current_width = _reading_width(size.columns)
        if current_width != width:
            state = _reflow_page(state, current_width)
            width = current_width
        clear_screen()
        _render(state, size)
        new_state = _next_state(get_page_text, state, width, size, prompt_input)
        if new_state is None:
            break
        state = new_state


def _next_state(
    get_page_text: GetPageText,
    state: PageState,
    width: int,
    size: terminal_size,
    prompt_input: PromptInput,
) -> PageState | None:
    try:
        key = _navigation_key(_read_key(), size.columns)
    except (KeyboardInterrupt, EOFError):
        return None
    new_state = handle_key(state, key, _body_rows(size.lines))
    if new_state.quit:
        return None
    new_state = _resolve_prompt(new_state, state.page, size.lines, prompt_input)
    if new_state.page != state.page:
        return _load_page(get_page_text, new_state, width=width)
    return new_state


def _resolve_prompt(
    state: PageState, current_page: int, terminal_rows: int, prompt_input: PromptInput
) -> PageState:
    if state.searching:
        print()
        query = prompt_input("/ ")
        state = set_search_query(state, query, _body_rows(terminal_rows))
    if not state.goto_page:
        return state
    print()
    raw = prompt_input(": ", default="")
    try:
        return jump_to_page(state, int(raw))
    except ValueError:
        return jump_to_page(state, current_page)


def _body_rows(rows: int) -> int:
    return max(1, rows - FRAME_ROWS)


def _frame_lines(state: PageState, size: terminal_size) -> list[str]:
    content_width = _reading_width(size.columns)
    padding = " " * max(0, (size.columns - content_width) // 2)
    body_rows = _body_rows(size.lines)
    visible = state.lines[state.scroll : state.scroll + body_rows]
    body = [f"{padding}{line}" for line in visible]
    body.extend([""] * (body_rows - len(body)))
    return [_header(state, size.columns), *body, _footer(state, size.columns)]


def _header(state: PageState, width: int) -> str:
    title = f" {state.title[: max(1, width - 4)]} "
    return title.center(width, "─")


def _footer(state: PageState, width: int) -> str:
    status = f" pág. {state.page}/{state.total_pages} "
    help_text = " ←/→ página · clique nos lados · ↑/↓ rolagem · q sai "
    text = f"{status}{help_text}"[:width]
    return text.center(width, "─")


def _render(state: PageState, size: terminal_size) -> None:
    """Print the current page and status bar to stdout."""
    print("\n".join(_frame_lines(state, size)), end="", flush=True)


def _read_key() -> str:
    """Read a single keypress from stdin (raw mode)."""
    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sequence = os.read(fd, 1)
        if sequence == b"\x1b":
            sequence += _read_escape_tail(fd)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return _normalize_key(sequence.decode("ascii", errors="ignore"))


def _read_escape_tail(fd: int) -> bytes:
    tail = bytearray()
    while len(tail) < 31 and select.select([fd], [], [], 0.01)[0]:
        tail.extend(os.read(fd, 1))
        if _sequence_complete(b"\x1b" + tail):
            break
    return bytes(tail)


def _sequence_complete(sequence: bytes) -> bool:
    if sequence.decode("ascii", errors="ignore") in ARROW_SEQUENCES:
        return True
    return sequence.startswith(b"\x1b[<") and sequence[-1:] in {b"M", b"m"}


def _normalize_key(sequence: str) -> str:
    mouse_key = _normalize_mouse(sequence)
    return mouse_key if mouse_key is not None else ARROW_SEQUENCES.get(sequence, sequence)


def _normalize_mouse(sequence: str) -> str | None:
    if not sequence.startswith("\x1b[<"):
        return None
    fields = sequence[3:-1].split(";")
    if len(fields) != 3 or not all(field.isdigit() for field in fields):
        return ""
    button, column, _row = (int(field) for field in fields)
    if not sequence.endswith("M"):
        return ""
    return {0: f"click:{column}", 64: "up", 65: "down"}.get(button, "")


def _navigation_key(key: str, columns: int) -> str:
    if not key.startswith("click:"):
        return key
    click_column = int(key.removeprefix("click:"))
    return "left" if click_column <= columns // 2 else "right"


def _set_mouse_tracking(enabled: bool) -> None:
    sequence = ENABLE_MOUSE_TRACKING if enabled else DISABLE_MOUSE_TRACKING
    print(sequence, end="", flush=True)
