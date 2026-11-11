"""Tests for the cache menu loop with scripted keys (no real terminal)."""

from __future__ import annotations

from os import terminal_size
from pathlib import Path

from labooke_bible._book_files import CacheCleared, CachedBook, cached_book_file
from labooke_bible._cache_menu import CacheMenuState
from labooke_bible._cache_tui import _menu_lines, format_size, run_cache_menu


class ScriptedKeys:
    """Returns predefined keypresses in order, then quits."""

    def __init__(self, *keys: str) -> None:
        self._keys = iter(keys)

    def __call__(self) -> str:
        return next(self._keys, "q")


class ScriptedPrompt:
    """Answers prompt_toolkit-style prompts from a fixed list."""

    def __init__(self, *answers: str) -> None:
        self._answers = iter(answers)
        self.questions: list[str] = []

    def __call__(self, message: str, **_: object) -> str:
        self.questions.append(message)
        return next(self._answers)


class CapturedScreen:
    """Collects every rendered frame instead of printing it."""

    def __init__(self) -> None:
        self.frames: list[list[str]] = []

    def __call__(self, lines: list[str]) -> None:
        self.frames.append(lines)


class OneFileDownloader:
    """Writes a 13-byte fake PDF for cache setup."""

    def download_file(self, book_id: int, destination: Path) -> None:
        destination.write_bytes(b"%PDF-1.7 fake")


def _fill_cache(cache_dir: Path) -> tuple[Path, Path]:
    keep = cached_book_file(
        OneFileDownloader(), {"id": 1, "format": "pdf", "sha256": "a", "title": "Alpha"}, cache_dir
    )
    drop = cached_book_file(
        OneFileDownloader(), {"id": 2, "format": "pdf", "sha256": "b", "title": "Beta"}, cache_dir
    )
    return keep, drop


def _run(cache_dir: Path, keys: ScriptedKeys, prompt: ScriptedPrompt) -> CacheCleared:
    return run_cache_menu(
        cache_dir, read_key=keys, prompt_input=prompt, show=CapturedScreen(), size=_size()
    )


def _size() -> terminal_size:
    return terminal_size((60, 10))


def test_marking_one_and_confirming_deletes_only_it(tmp_path: Path) -> None:
    keep, drop = _fill_cache(tmp_path)

    cleared = _run(tmp_path, ScriptedKeys("j", " ", "\r"), ScriptedPrompt("y"))

    assert cleared == CacheCleared(files=1, size_bytes=13)
    assert keep.exists() and not drop.exists()


def test_declining_confirmation_keeps_files(tmp_path: Path) -> None:
    keep, drop = _fill_cache(tmp_path)

    cleared = _run(tmp_path, ScriptedKeys("a", "\r"), ScriptedPrompt("n"))

    assert cleared == CacheCleared(files=0, size_bytes=0)
    assert keep.exists() and drop.exists()


def test_search_then_mark_all_deletes_only_matches(tmp_path: Path) -> None:
    keep, drop = _fill_cache(tmp_path)

    _run(tmp_path, ScriptedKeys("/", "a", "\r"), ScriptedPrompt("bet", "y"))

    assert keep.exists() and not drop.exists()


def test_quitting_without_marks_deletes_nothing(tmp_path: Path) -> None:
    keep, drop = _fill_cache(tmp_path)

    assert _run(tmp_path, ScriptedKeys("q"), ScriptedPrompt()) == CacheCleared(0, 0)
    assert keep.exists() and drop.exists()


def test_menu_lines_show_cursor_marks_sizes_and_total() -> None:
    books = (
        CachedBook(Path("a.pdf"), "Alpha", 2048),
        CachedBook(Path("b.pdf"), "Beta", 3 * 1024 * 1024),
    )
    state = CacheMenuState(books=books, cursor=1, marked=frozenset({Path("b.pdf")}))

    lines = _menu_lines(state, _size())

    assert any(line.startswith("  [ ] Alpha") and "2.0 KiB" in line for line in lines)
    assert any(line.startswith("> [x] Beta") and "3.0 MiB" in line for line in lines)
    assert "1 marcado(s) (3.0 MiB)" in lines[-1]


def test_menu_lines_say_when_filter_matches_nothing() -> None:
    state = CacheMenuState(books=(CachedBook(Path("a.pdf"), "Alpha", 1),), query="zzz")

    assert any("nada encontrado para 'zzz'" in line for line in _menu_lines(state, _size()))


def test_format_size_picks_readable_unit() -> None:
    assert [format_size(n) for n in (512, 2048, 5 * 1024**3)] == ["512 B", "2.0 KiB", "5.0 GiB"]
