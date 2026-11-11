"""Local cache of raw book files downloaded from the labooke API.

Files are named by sha256, so the same book is downloaded once and a
changed file on the server gets a new cache entry. ``index.json`` maps
each file name to the book title so ``bible cache`` can show titles.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

_INDEX_NAME = "index.json"


class BookFileDownloader(Protocol):
    """The part of ``ApiClient`` that fetches a book's raw file."""

    def download_file(self, book_id: int, destination: Path) -> None:
        """Write the raw file of ``book_id`` to ``destination``."""
        ...


@dataclass(frozen=True, slots=True)
class CachedBook:
    """One file in the cache, as listed by ``bible cache``."""

    path: Path
    title: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class CacheCleared:
    """How much ``delete_cached_books`` removed."""

    files: int
    size_bytes: int


def default_cache_dir() -> Path:
    """Return ``$XDG_CACHE_HOME/labooke/books`` (``~/.cache`` fallback)."""
    root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "labooke" / "books"


def cached_book_file(downloader: BookFileDownloader, book: dict, cache_dir: Path) -> Path:
    """Return a local copy of ``book``'s file, downloading it if missing.

    Example:
        >>> cached_book_file(client, book, default_cache_dir())  # doctest: +SKIP
    """
    target = cache_dir / f"{book['sha256']}.{book['format']}"
    if target.exists():
        return target
    cache_dir.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    try:
        downloader.download_file(book["id"], partial)
    except BaseException:
        # Drop the half-written file so the next run downloads it again.
        partial.unlink(missing_ok=True)
        raise
    partial.replace(target)
    _write_index(cache_dir, {**_read_index(cache_dir), target.name: str(book.get("title", ""))})
    return target


def list_cached_books(cache_dir: Path) -> list[CachedBook]:
    """Return every cached file sorted by title (file name when unknown).

    Example:
        >>> list_cached_books(Path("/nonexistent"))
        []
    """
    if not cache_dir.is_dir():
        return []
    titles = _read_index(cache_dir)
    books = [
        CachedBook(path, titles.get(path.name) or path.name, path.stat().st_size)
        for path in cache_dir.iterdir()
        if path.is_file() and path.name != _INDEX_NAME
    ]
    return sorted(books, key=lambda book: book.title.casefold())


def delete_cached_books(cache_dir: Path, paths: Iterable[Path]) -> CacheCleared:
    """Delete ``paths`` from the cache and drop their titles from the index."""
    titles = _read_index(cache_dir)
    files = size = 0
    for path in paths:
        size += path.stat().st_size
        path.unlink()
        titles.pop(path.name, None)
        files += 1
    _write_index(cache_dir, titles)
    return CacheCleared(files=files, size_bytes=size)


def _read_index(cache_dir: Path) -> dict[str, str]:
    index = cache_dir / _INDEX_NAME
    if not index.exists():
        return {}
    try:
        return dict(json.loads(index.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(
            f"corrupt cache index {index}: {exc}; expected a JSON object "
            "of file name -> title (delete the file to rebuild it)"
        ) from exc


def _write_index(cache_dir: Path, titles: dict[str, str]) -> None:
    if not cache_dir.is_dir():
        return
    index = cache_dir / _INDEX_NAME
    index.write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")
