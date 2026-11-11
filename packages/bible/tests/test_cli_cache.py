"""Tests for `bible cache` wiring in the CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from labooke_bible._book_files import CacheCleared
from labooke_bible.cli import app
from typer.testing import CliRunner

runner = CliRunner()


class RecordingCacheMenu:
    """Stands in for the interactive menu and returns a fixed result."""

    def __init__(self, result: CacheCleared) -> None:
        self.opened: list[Path] = []
        self._result = result

    def __call__(self, cache_dir: Path) -> CacheCleared:
        self.opened.append(cache_dir)
        return self._result


@pytest.fixture(autouse=True)
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    return tmp_path / "labooke" / "books"


def test_cache_on_empty_dir_says_so_without_opening_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    menu = RecordingCacheMenu(CacheCleared(0, 0))
    monkeypatch.setattr("labooke_bible.cli._cache_menu_runner", menu)

    result = runner.invoke(app, ["cache"])

    assert result.exit_code == 0
    assert "Cache is empty" in result.output
    assert menu.opened == []


def test_cache_opens_menu_and_reports_freed_space(
    cache_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_dir.mkdir(parents=True)
    (cache_dir / "a.pdf").write_bytes(b"x")
    menu = RecordingCacheMenu(CacheCleared(files=2, size_bytes=2048))
    monkeypatch.setattr("labooke_bible.cli._cache_menu_runner", menu)

    result = runner.invoke(app, ["cache"])

    assert result.exit_code == 0, result.output
    assert menu.opened == [cache_dir]
    assert "Deleted 2 file(s), freed 2.0 KiB" in result.output
