"""Tests for ApiClient.download_file streaming the raw book file."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from labooke_bible._api_client import ApiClient, ApiError


def _client_with(handler: httpx.MockTransport) -> ApiClient:
    return ApiClient("http://api.test", http=httpx.Client(transport=handler))


def test_download_file_writes_response_bytes(tmp_path: Path) -> None:
    seen: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, content=b"%PDF-1.7 body")

    destination = tmp_path / "book.pdf"
    _client_with(httpx.MockTransport(respond)).download_file(4, destination)

    assert seen == ["/api/books/4/file"]
    assert destination.read_bytes() == b"%PDF-1.7 body"


def test_download_file_raises_api_error_on_404(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Book file not found"})

    with pytest.raises(ApiError, match="HTTP 404: Book file not found"):
        _client_with(httpx.MockTransport(respond)).download_file(4, tmp_path / "x.pdf")
