"""Happy-path coverage for the ``/api/books`` endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from labooke_api.container import AppContainer
from labooke_core.domain.models import BookStatus


def _insert_book(container: AppContainer, *, sha256: str, title: str) -> int:
    book = container.books.insert(
        sha256=sha256,
        path=Path(f"/tmp/{sha256}.pdf"),
        title=title,
        format="pdf",
        status=BookStatus.READY,
    )
    return book.id


def test_list_books_empty_then_populated(
    client: TestClient, container: AppContainer
) -> None:
    assert client.get("/api/books").json() == {"items": []}
    book_id = _insert_book(container, sha256="a", title="Alpha")
    payload = client.get("/api/books").json()
    assert [item["id"] for item in payload["items"]] == [book_id]


def test_get_book_returns_404_when_missing(client: TestClient) -> None:
    response = client.get("/api/books/9999")
    assert response.status_code == 404
    assert response.json()["code"] == "book_not_found"


def test_attach_then_detach_tag(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="b", title="Beta")
    tag = client.post(
        "/api/tags", json={"name": "Linux", "slug": "linux", "color": "#000"}
    ).json()

    attached = client.post(
        f"/api/books/{book_id}/tags", json={"tag_id": tag["id"]}
    ).json()
    assert [t["slug"] for t in attached["tags"]] == ["linux"]

    detached = client.delete(f"/api/books/{book_id}/tags/{tag['id']}").json()
    assert detached["tags"] == []


def test_patch_book_renames_title(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="r", title="Old")
    response = client.patch(f"/api/books/{book_id}", json={"title": "New"})
    assert response.status_code == 200
    assert response.json()["title"] == "New"
    assert client.get(f"/api/books/{book_id}").json()["title"] == "New"


def test_patch_book_rejects_empty_title(
    client: TestClient, container: AppContainer
) -> None:
    book_id = _insert_book(container, sha256="r2", title="Keep")
    assert client.patch(f"/api/books/{book_id}", json={"title": ""}).status_code == 422


def test_patch_book_404_when_missing(client: TestClient) -> None:
    assert client.patch("/api/books/9999", json={"title": "X"}).status_code == 404


def test_delete_book_removes_it(client: TestClient, container: AppContainer) -> None:
    book_id = _insert_book(container, sha256="c", title="Gamma")
    assert client.delete(f"/api/books/{book_id}").status_code == 204
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_filter_books_by_tag(client: TestClient, container: AppContainer) -> None:
    a = _insert_book(container, sha256="d", title="Delta")
    _insert_book(container, sha256="e", title="Epsilon")
    tag = client.post(
        "/api/tags", json={"name": "Sci", "slug": "sci", "color": "#000"}
    ).json()
    client.post(f"/api/books/{a}/tags", json={"tag_id": tag["id"]})

    response = client.get("/api/books", params={"tags": tag["id"]})
    assert [item["id"] for item in response.json()["items"]] == [a]
