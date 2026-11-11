"""Tests for the local cache of downloaded book files."""

from __future__ import annotations

from pathlib import Path

import pytest
from labooke_bible._book_files import (
    CacheCleared,
    cached_book_file,
    delete_cached_books,
    list_cached_books,
)


class CountingFileDownloader:
    """Writes fake PDF bytes and counts how many downloads happened."""

    def __init__(self) -> None:
        self.downloads: list[tuple[int, Path]] = []

    def download_file(self, book_id: int, destination: Path) -> None:
        self.downloads.append((book_id, destination))
        destination.write_bytes(b"%PDF-1.7 fake")


def _book(sha: str = "abc123", title: str = "Manual") -> dict:
    return {"id": 7, "format": "pdf", "sha256": sha, "title": title}


def test_downloads_into_cache_named_by_sha(tmp_path: Path) -> None:
    downloader = CountingFileDownloader()

    path = cached_book_file(downloader, _book(), tmp_path / "cache")

    assert path == tmp_path / "cache" / "abc123.pdf"
    assert path.read_bytes() == b"%PDF-1.7 fake"
    assert len(downloader.downloads) == 1


def test_reuses_cached_file_without_downloading_again(tmp_path: Path) -> None:
    downloader = CountingFileDownloader()
    cached_book_file(downloader, _book(), tmp_path)

    cached_book_file(downloader, _book(), tmp_path)

    assert len(downloader.downloads) == 1


def test_leaves_no_partial_file_when_download_fails(tmp_path: Path) -> None:
    class FailingFileDownloader:
        """Writes half a file, then fails like a dropped connection."""

        def download_file(self, book_id: int, destination: Path) -> None:
            destination.write_bytes(b"half")
            raise OSError("connection reset")

    with pytest.raises(OSError, match="connection reset"):
        cached_book_file(FailingFileDownloader(), _book(), tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_lists_cached_books_with_titles_and_sizes(tmp_path: Path) -> None:
    downloader = CountingFileDownloader()
    cached_book_file(downloader, _book("bbb", "Zeta"), tmp_path)
    cached_book_file(downloader, _book("aaa", "Alpha"), tmp_path)

    listed = list_cached_books(tmp_path)

    assert [(c.title, c.path.name, c.size_bytes) for c in listed] == [
        ("Alpha", "aaa.pdf", 13),
        ("Zeta", "bbb.pdf", 13),
    ]


def test_lists_unknown_files_by_name(tmp_path: Path) -> None:
    (tmp_path / "orphan.pdf").write_bytes(b"x")

    assert [c.title for c in list_cached_books(tmp_path)] == ["orphan.pdf"]


def test_list_on_missing_dir_is_empty(tmp_path: Path) -> None:
    assert list_cached_books(tmp_path / "nope") == []


def test_delete_removes_only_chosen_files_and_their_titles(tmp_path: Path) -> None:
    downloader = CountingFileDownloader()
    keep = cached_book_file(downloader, _book("aaa", "Keep"), tmp_path)
    drop = cached_book_file(downloader, _book("bbb", "Drop"), tmp_path)

    cleared = delete_cached_books(tmp_path, [drop])

    assert cleared == CacheCleared(files=1, size_bytes=13)
    assert keep.exists() and not drop.exists()
    assert [c.title for c in list_cached_books(tmp_path)] == ["Keep"]
