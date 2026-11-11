"""``bible cache`` menu state machine — pure logic, no terminal.

Mirrors ``_pager.py``: ``handle_cache_key`` turns one keypress into a
new immutable state, and ``_cache_tui.py`` only draws and reads keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from labooke_bible._book_files import CachedBook


@dataclass(frozen=True)
class CacheMenuState:
    """Snapshot of the cache menu.

    Example:
        >>> CacheMenuState(books=()).visible()
        []
    """

    books: tuple[CachedBook, ...]
    query: str = ""
    cursor: int = 0
    marked: frozenset[Path] = field(default_factory=frozenset)
    searching: bool = False
    confirming: bool = False
    quit: bool = False

    def visible(self) -> list[CachedBook]:
        """Books whose title contains the search query (any case)."""
        needle = self.query.casefold()
        return [book for book in self.books if needle in book.title.casefold()]

    def marked_size(self) -> int:
        """Total bytes of the marked books."""
        return sum(book.size_bytes for book in self.books if book.path in self.marked)


def handle_cache_key(state: CacheMenuState, key: str) -> CacheMenuState:
    """Return the state after one keypress.

    Example:
        >>> handle_cache_key(CacheMenuState(books=()), "q").quit
        True
    """
    if key in {"j", "k", "up", "down"}:
        return _move_cursor(state, 1 if key in {"j", "down"} else -1)
    if key in {" ", "a", "u"}:
        return _change_marks(state, key)
    if key in {"\r", "\n"}:
        return replace(state, confirming=bool(state.marked))
    if key == "/":
        return replace(state, searching=True)
    if key in {"q", "\x1b", "\x03"}:
        return replace(state, quit=True)
    return state


def set_filter(state: CacheMenuState, query: str) -> CacheMenuState:
    """Apply a search query and bring the cursor back to the first row."""
    return replace(state, query=query.strip(), cursor=0, searching=False)


def _move_cursor(state: CacheMenuState, step: int) -> CacheMenuState:
    last = max(0, len(state.visible()) - 1)
    return replace(state, cursor=max(0, min(state.cursor + step, last)))


def _change_marks(state: CacheMenuState, key: str) -> CacheMenuState:
    visible = state.visible()
    if key == "u":
        return replace(state, marked=frozenset())
    if key == "a":
        return replace(state, marked=state.marked | {book.path for book in visible})
    if not visible:
        return state
    return replace(state, marked=state.marked ^ {visible[state.cursor].path})
