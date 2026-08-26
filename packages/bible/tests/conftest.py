"""Shared fixtures for bible CLI tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from labooke_bible._api_client import ApiError
from labooke_bible._history import HistoryStore


class FakeApiClient:
    """In-memory fake that mimics the real ApiClient HTTP interface."""

    def __init__(self) -> None:
        self._tags: dict[int, dict] = {}
        self._books: dict[int, dict] = {}
        self._tag_seq = 0
        self._book_seq = 0
        self._scan_result: dict = {"ingested": 0, "skipped": 0, "failed": 0}

    def add_tag(self, name: str, slug: str, color: str = "#888") -> dict:
        self._tag_seq += 1
        t = {"id": self._tag_seq, "name": name, "slug": slug, "color": color}
        self._tags[self._tag_seq] = t
        return t

    def add_book(
        self, title: str, fmt: str = "txt", tag_ids: list[int] | None = None
    ) -> dict:
        self._book_seq += 1
        b = {
            "id": self._book_seq,
            "title": title,
            "format": fmt,
            "tag_ids": set(tag_ids or []),
        }
        self._books[self._book_seq] = b
        return {"id": b["id"], "title": title, "format": fmt}

    def set_scan_result(
        self, *, ingested: int = 0, skipped: int = 0, failed: int = 0
    ) -> None:
        self._scan_result = {"ingested": ingested, "skipped": skipped, "failed": failed}

    def _book_out(self, b: dict) -> dict:
        tags = [self._tags[tid] for tid in b["tag_ids"] if tid in self._tags]
        return {
            "id": b["id"],
            "title": b["title"],
            "format": b["format"],
            "tags": tags,
            "page_count": 5,
        }

    # ── ApiClient interface ────────────────────────────────────────────────────

    def get_tags(self) -> list[dict]:
        result = []
        for t in self._tags.values():
            count = sum(1 for b in self._books.values() if t["id"] in b["tag_ids"])
            result.append({"tag": t, "count": count})
        return result

    def get_books(self, tag_ids: list[int] | None = None) -> list[dict]:
        books = list(self._books.values())
        if tag_ids:
            books = [b for b in books if all(tid in b["tag_ids"] for tid in tag_ids)]
        return [self._book_out(b) for b in books]

    def get_book(self, book_id: int) -> dict:
        if book_id not in self._books:
            raise ApiError(404, "Not found")
        return self._book_out(self._books[book_id])

    def attach_tag(self, book_id: int, tag_id: int) -> None:
        self._books[book_id]["tag_ids"].add(tag_id)

    def detach_tag(self, book_id: int, tag_id: int) -> None:
        self._books[book_id]["tag_ids"].discard(tag_id)

    def search(
        self,
        query: str,
        *,
        mode: str = "semantic",
        tag_ids: list[int] | None = None,
        tag_mode: str = "all",
        k: int = 10,
    ) -> list[dict]:
        hits = []
        for b in self._books.values():
            if query.lower() not in b["title"].lower():
                continue
            if tag_ids:
                if tag_mode == "all" and not all(
                    tid in b["tag_ids"] for tid in tag_ids
                ):
                    continue
                if tag_mode == "any" and not any(
                    tid in b["tag_ids"] for tid in tag_ids
                ):
                    continue
            hits.append({"book_id": b["id"], "page_start": 1, "snippet": b["title"]})
        return hits[:k]

    def get_page(self, book_id: int, page_no: int) -> str:
        return "page text"

    def scan(self) -> dict:
        return self._scan_result


@pytest.fixture
def fake_client() -> FakeApiClient:
    return FakeApiClient()


@pytest.fixture
def fake_history(tmp_path: Path) -> HistoryStore:
    return HistoryStore(tmp_path / "bible_history.txt")


@pytest.fixture(autouse=True)
def inject_client(
    fake_client: FakeApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("labooke_bible.cli._client_singleton", fake_client)


@pytest.fixture(autouse=True)
def inject_history(
    fake_history: HistoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("labooke_bible.cli._history_singleton", fake_history)
