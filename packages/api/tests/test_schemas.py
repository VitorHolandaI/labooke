"""Tests for the schema mappers in :mod:`labooke_api.schemas`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from labooke_api.schemas import (
    BookmarkOut,
    BookOut,
    PageTextOut,
    ProgressOut,
    ScanResultOut,
    SearchHitOut,
    TagOut,
)
from labooke_core.domain.models import (
    Book,
    Bookmark,
    BookStatus,
    PageText,
    ReadingProgress,
    SearchHit,
    Tag,
)
from labooke_core.services import ScanResult


def test_tag_out_round_trip():
    tag = Tag(id=1, name="Linux", slug="linux", color="#22c55e")
    payload = TagOut.from_domain(tag).model_dump()
    assert payload == {"id": 1, "name": "Linux", "slug": "linux", "color": "#22c55e"}


def test_book_out_serializes_tags_and_status():
    tag = Tag(id=2, name="Fiction", slug="fiction", color="#888888")
    book = Book(
        id=10,
        sha256="abc",
        path=Path("/data/books/abc.pdf"),
        title="Demo",
        format="pdf",
        page_count=4,
        status=BookStatus.READY,
        tags=[tag],
    )
    payload = BookOut.from_domain(book).model_dump()
    assert payload["status"] == "ready"
    assert payload["tags"] == [TagOut.from_domain(tag).model_dump()]
    assert "path" not in payload
    assert "sha256" in payload


def test_page_and_bookmark_and_progress_mappers():
    page = PageTextOut.from_domain(PageText(page_no=3, text="hi"))
    bookmark = BookmarkOut.from_domain(
        Bookmark(id=1, book_id=2, page_no=5, label="ch1", note=None)
    )
    progress = ProgressOut.from_domain(
        ReadingProgress(book_id=2, page_no=7, updated_at=datetime(2026, 1, 1))
    )
    assert page.text == "hi"
    assert bookmark.label == "ch1"
    assert progress.page_no == 7


def test_search_hit_and_scan_result_mappers():
    hit = SearchHitOut.from_domain(
        SearchHit(book_id=1, page_start=1, page_end=2, snippet="x", score=0.9)
    )
    scan = ScanResultOut.from_domain(ScanResult(ingested=3, skipped=1, failed=0))
    assert hit.score == 0.9
    assert scan.model_dump() == {"ingested": 3, "skipped": 1, "failed": 0}
