"""Terminal loop for ``bible cache``: draw the list, read keys, delete.

Keys and screen are injected so tests drive the loop with scripted
input; the defaults reuse the raw-mode key reader from ``_tui.py``.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import replace
from os import terminal_size
from pathlib import Path

from labooke_bible._book_files import CacheCleared, delete_cached_books, list_cached_books
from labooke_bible._cache_menu import CacheMenuState, handle_cache_key, set_filter
from labooke_bible._tui import _read_key

PromptInput = Callable[..., str]
ShowFrame = Callable[[list[str]], None]
_SIZE_COLUMN = 10
_HELP = "␣ marca · a todos · u nenhum · / busca · ⏎ apaga · q sai"


def format_size(size_bytes: int) -> str:
    """Human-readable size, e.g. ``format_size(2048) == '2.0 KiB'``."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    value = float(size_bytes)
    for unit in ("KiB", "MiB", "GiB"):
        value /= 1024
        if value < 1024 or unit == "GiB":
            break
    return f"{value:.1f} {unit}"


def run_cache_menu(
    cache_dir: Path,
    *,
    read_key: Callable[[], str] = _read_key,
    prompt_input: PromptInput | None = None,
    show: ShowFrame | None = None,
    size: terminal_size | None = None,
) -> CacheCleared:
    """Let the user pick cached files to delete; return what was removed.

    Example:
        >>> run_cache_menu(default_cache_dir())  # doctest: +SKIP
    """
    ask = prompt_input or _default_prompt()
    draw = show or _print_frame
    state = CacheMenuState(books=tuple(list_cached_books(cache_dir)))
    while True:
        draw(_menu_lines(state, size or shutil.get_terminal_size((80, 24))))
        state = handle_cache_key(state, read_key())
        if state.quit:
            return CacheCleared(files=0, size_bytes=0)
        if state.searching:
            state = set_filter(state, ask("/ ", default=state.query))
        if state.confirming and _confirmed(state, ask):
            return delete_cached_books(cache_dir, sorted(state.marked))
        state = replace(state, confirming=False)


def _confirmed(state: CacheMenuState, ask: PromptInput) -> bool:
    question = f"Apagar {len(state.marked)} arquivo(s), {format_size(state.marked_size())}? [y/N] "
    return ask(question).strip().lower() in {"y", "yes", "s", "sim"}


def _menu_lines(state: CacheMenuState, size: terminal_size) -> list[str]:
    """Header, the rows that fit around the cursor, then the status bar."""
    width = size.columns
    body_rows = max(1, size.lines - 2)
    visible = state.visible()
    start = max(0, min(state.cursor - body_rows + 1, len(visible) - body_rows))
    rows = [
        _row(state, book.path, book.title, book.size_bytes, index == state.cursor, width)
        for index, book in enumerate(visible[start : start + body_rows], start)
    ]
    if not visible:
        rows = [f"  nada encontrado para {state.query!r}" if state.query else "  (cache vazio)"]
    rows.extend([""] * (body_rows - len(rows)))
    return [_header(state, width), *rows, _footer(state, width)]


def _row(
    state: CacheMenuState, path: Path, title: str, size_bytes: int, current: bool, width: int
) -> str:
    pointer = ">" if current else " "
    mark = "x" if path in state.marked else " "
    room = max(1, width - 6 - _SIZE_COLUMN)
    return f"{pointer} [{mark}] {title[:room]:<{room}}{format_size(size_bytes):>{_SIZE_COLUMN}}"


def _header(state: CacheMenuState, width: int) -> str:
    search = f" · busca: {state.query}" if state.query else ""
    return f" cache do bible: {len(state.books)} PDF(s){search} "[:width].center(width, "─")


def _footer(state: CacheMenuState, width: int) -> str:
    summary = f" {len(state.marked)} marcado(s) ({format_size(state.marked_size())}) · "
    return f"{summary}{_HELP} "[:width].center(width, "─")


def _print_frame(lines: list[str]) -> None:
    from prompt_toolkit.shortcuts import clear

    clear()
    print("\n".join(lines), end="", flush=True)


def _default_prompt() -> PromptInput:
    from prompt_toolkit.shortcuts import prompt

    def ask(message: str, default: str = "") -> str:
        print()
        return prompt(message, default=default)

    return ask
