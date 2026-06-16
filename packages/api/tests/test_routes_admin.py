"""Coverage for the admin maintenance endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _upload(client: TestClient, name: str) -> dict:
    files = {"file": (name, b"chapter one\nchapter two\n", "text/plain")}
    response = client.post("/api/books", files=files)
    assert response.status_code == 202, response.text
    return response.json()


def test_admin_scan_ingests_inbox(client_with_fake_pipeline):
    client, fake = client_with_fake_pipeline
    inbox = client.app.state.container.settings.import_dir
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / "one.txt").write_text("alpha", encoding="utf-8")
    (inbox / "two.md").write_text("beta", encoding="utf-8")

    result = client.post("/api/admin/scan").json()
    assert result == {"ingested": 2, "skipped": 0, "failed": 0}
    assert len(fake.rebuilt_books) == 2


def test_reembed_book_returns_202(client_with_fake_pipeline):
    client, fake = client_with_fake_pipeline
    payload = _upload(client, "demo.txt")
    fake.rebuilt_books.clear()

    response = client.post(f"/api/books/{payload['book_id']}/reembed")
    assert response.status_code == 202
    assert fake.rebuilt_books == [payload["book_id"]]


def test_reembed_all_returns_one_payload_per_book(client_with_fake_pipeline):
    client, fake = client_with_fake_pipeline
    first = _upload(client, "a.txt")
    second = _upload(client, "b.txt")
    fake.rebuilt_books.clear()

    response = client.post("/api/admin/reembed-all")
    body = response.json()
    assert {entry["book_id"] for entry in body} == {first["book_id"], second["book_id"]}
    assert sorted(fake.rebuilt_books) == sorted({first["book_id"], second["book_id"]})
