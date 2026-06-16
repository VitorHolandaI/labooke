"""Coverage for the upload endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _post_upload(client: TestClient, name: str, tag_ids: list[int] | None = None) -> dict:
    files = {"file": (name, b"chapter one\nchapter two\n", "text/plain")}
    kwargs: dict = {"files": files}
    if tag_ids:
        kwargs["data"] = {"tag_ids": [str(tag_id) for tag_id in tag_ids]}
    response = client.post("/api/books", **kwargs)
    assert response.status_code == 202, response.text
    return response.json()


def test_upload_creates_book_and_runs_pipeline(client_with_fake_pipeline):
    client, fake = client_with_fake_pipeline
    payload = _post_upload(client, "demo.txt")
    assert payload["status"] == "pending"
    assert fake.rebuilt_books == [payload["book_id"]]

    book = client.get(f"/api/books/{payload['book_id']}").json()
    assert book["status"] == "ready"


def test_upload_dedups_by_sha256(client_with_fake_pipeline):
    client, fake = client_with_fake_pipeline
    first = _post_upload(client, "demo.txt")
    second = _post_upload(client, "demo.txt")
    assert first["book_id"] == second["book_id"]
    assert fake.rebuilt_books == [first["book_id"]]


def test_upload_duplicate_merges_tags(client_with_fake_pipeline):
    client, _ = client_with_fake_pipeline
    sci = client.post(
        "/api/tags", json={"name": "Sci", "slug": "sci", "color": "#000"}
    ).json()
    fic = client.post(
        "/api/tags", json={"name": "Fic", "slug": "fic", "color": "#000"}
    ).json()

    first = _post_upload(client, "shared.txt", tag_ids=[sci["id"]])
    second = _post_upload(client, "shared.txt", tag_ids=[fic["id"]])
    assert first["book_id"] == second["book_id"]

    book = client.get(f"/api/books/{first['book_id']}").json()
    assert {tag["slug"] for tag in book["tags"]} == {"sci", "fic"}
