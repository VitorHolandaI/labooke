"""Smoke-test the OpenAPI surface so route drift fails CI early."""

from __future__ import annotations

from fastapi.testclient import TestClient

EXPECTED_PATHS = {
    "/api/tags",
    "/api/tags/{tag_id}",
    "/api/tags/merge",
    "/api/books",
    "/api/books/{book_id}",
    "/api/books/{book_id}/tags",
    "/api/books/{book_id}/tags/{tag_id}",
    "/api/books/{book_id}/bookmarks",
    "/api/bookmarks/{bookmark_id}",
    "/api/books/{book_id}/progress",
    "/api/books/{book_id}/pages/{page_no}",
    "/api/books/{book_id}/file",
    "/api/books/{book_id}/cover",
    "/api/books/{book_id}/reembed",
    "/api/search",
    "/api/admin/scan",
    "/api/admin/reembed-all",
}


def test_openapi_advertises_every_route(client: TestClient):
    paths = set(client.get("/openapi.json").json()["paths"].keys())
    missing = EXPECTED_PATHS - paths
    assert not missing, f"missing OpenAPI paths: {sorted(missing)}"


def test_docs_endpoint_serves_swagger_ui(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
