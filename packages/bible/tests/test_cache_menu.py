"""Tests for the cache menu state machine (pure, no terminal)."""

from __future__ import annotations

from pathlib import Path

from labooke_bible._book_files import CachedBook
from labooke_bible._cache_menu import CacheMenuState, handle_cache_key, set_filter


def _state() -> CacheMenuState:
    books = (
        CachedBook(Path("a.pdf"), "Linux Kernel", 10),
        CachedBook(Path("b.pdf"), "Rust Book", 20),
        CachedBook(Path("c.pdf"), "Linux Admin", 30),
    )
    return CacheMenuState(books=books)


def test_space_toggles_mark_on_cursor_row() -> None:
    state = handle_cache_key(_state(), " ")
    assert state.marked == frozenset({Path("a.pdf")})
    assert handle_cache_key(state, " ").marked == frozenset()


def test_cursor_moves_within_bounds() -> None:
    state = handle_cache_key(_state(), "k")
    assert state.cursor == 0
    state = handle_cache_key(handle_cache_key(handle_cache_key(state, "j"), "down"), "j")
    assert state.cursor == 2


def test_filter_matches_title_case_insensitively() -> None:
    state = set_filter(_state(), "linux")
    assert [b.title for b in state.visible()] == ["Linux Kernel", "Linux Admin"]


def test_mark_all_marks_only_visible_rows() -> None:
    state = handle_cache_key(set_filter(_state(), "linux"), "a")
    assert state.marked == frozenset({Path("a.pdf"), Path("c.pdf")})


def test_unmark_all_clears_marks() -> None:
    state = handle_cache_key(handle_cache_key(_state(), "a"), "u")
    assert state.marked == frozenset()


def test_filter_resets_cursor_into_visible_range() -> None:
    state = handle_cache_key(handle_cache_key(_state(), "j"), "j")
    assert set_filter(state, "rust").cursor == 0


def test_space_on_empty_filter_does_nothing() -> None:
    state = handle_cache_key(set_filter(_state(), "zzz"), " ")
    assert state.marked == frozenset()


def test_enter_requests_confirmation_only_when_something_is_marked() -> None:
    assert handle_cache_key(_state(), "\r").confirming is False
    marked = handle_cache_key(_state(), " ")
    assert handle_cache_key(marked, "\r").confirming is True


def test_marked_size_sums_marked_books() -> None:
    state = handle_cache_key(_state(), "a")
    assert state.marked_size() == 60


def test_slash_starts_search_and_q_quits() -> None:
    assert handle_cache_key(_state(), "/").searching is True
    assert handle_cache_key(_state(), "q").quit is True
