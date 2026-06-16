"""Happy-path coverage for the ``/api/tags`` endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_tags_includes_seeded_set(client: TestClient):
    response = client.get("/api/tags")
    assert response.status_code == 200
    payload = response.json()
    slugs = {entry["tag"]["slug"] for entry in payload}
    assert {"fiction", "science", "programming"} <= slugs


def test_create_then_patch_then_delete_tag(client: TestClient):
    created = client.post(
        "/api/tags", json={"name": "Linux", "slug": "linux", "color": "#000000"}
    ).json()
    assert created["slug"] == "linux"

    patched = client.patch(
        f"/api/tags/{created['id']}", json={"name": "Linux x86", "color": "#ffffff"}
    ).json()
    assert patched == {**created, "name": "Linux x86", "color": "#ffffff"}

    deleted = client.delete(f"/api/tags/{created['id']}")
    assert deleted.status_code == 204

    slugs = {entry["tag"]["slug"] for entry in client.get("/api/tags").json()}
    assert "linux" not in slugs


def test_patch_unknown_tag_returns_404(client: TestClient):
    response = client.patch("/api/tags/9999", json={"name": "x"})
    assert response.status_code == 404
    assert response.json()["code"] == "tag_not_found"


def test_merge_tags_moves_attachments(client: TestClient):
    src = client.post(
        "/api/tags", json={"name": "Old", "slug": "old", "color": "#000"}
    ).json()
    dst = client.post(
        "/api/tags", json={"name": "New", "slug": "new", "color": "#000"}
    ).json()

    response = client.post(
        "/api/tags/merge", json={"source_id": src["id"], "target_id": dst["id"]}
    )
    assert response.status_code == 204

    slugs = {entry["tag"]["slug"] for entry in client.get("/api/tags").json()}
    assert "old" not in slugs and "new" in slugs
