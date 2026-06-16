"""Coverage for the reader (pages/file/cover) routes."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus


def _stage_text_book(container: AppContainer, tmp_path: Path) -> tuple[int, Path]:
    book_path = tmp_path / "demo.txt"
    book_path.write_text("hello\nworld\n", encoding="utf-8")
    book = container.books.insert(
        sha256="reader-1",
        path=book_path,
        title="Reader Demo",
        format="txt",
        page_count=1,
        status=BookStatus.READY,
    )
    return book.id, book_path


def test_get_page_returns_extracted_text(
    client: TestClient, container: AppContainer, tmp_path: Path
) -> None:
    book_id, _ = _stage_text_book(container, tmp_path)
    response = client.get(f"/api/books/{book_id}/pages/1")
    assert response.status_code == 200
    body = response.json()
    assert body["page_no"] == 1
    assert "hello" in body["text"]


def test_get_book_file_streams_bytes(
    client: TestClient, container: AppContainer, tmp_path: Path
) -> None:
    book_id, book_path = _stage_text_book(container, tmp_path)
    response = client.get(f"/api/books/{book_id}/file")
    assert response.status_code == 200
    assert response.content == book_path.read_bytes()


def test_get_book_cover_generates_and_caches(
    client: TestClient, container: AppContainer, tmp_path: Path
) -> None:
    book_id, _ = _stage_text_book(container, tmp_path)
    cover_path = container.settings.covers_dir / "reader-1.webp"
    assert not cover_path.exists()

    response = client.get(f"/api/books/{book_id}/cover")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert cover_path.exists()


def test_get_page_invalid_returns_400(
    client: TestClient, container: AppContainer, tmp_path: Path
) -> None:
    book_id, _ = _stage_text_book(container, tmp_path)
    response = client.get(f"/api/books/{book_id}/pages/999")
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_argument"
