"""Thin sync HTTP client for the labooke API."""

from __future__ import annotations

import os
from typing import Any

import httpx


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class ApiClient:
    """Wraps every labooke API endpoint used by the bible CLI.

    Base URL is read from the ``LABOOKE_API_URL`` env var
    (default: ``http://localhost:8000``).

    Example:
        >>> ApiClient("http://localhost:8000")._base
        'http://localhost:8000'
    """

    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        base = base_url or os.environ.get("LABOOKE_API_URL") or "http://localhost:8000"
        self._base = base.rstrip("/")
        self._timeout = timeout

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> Any:
        try:
            resp = httpx.get(f"{self._base}{path}", params=params or {}, timeout=self._timeout)
        except httpx.TransportError as exc:
            raise ApiError(0, str(exc)) from exc
        _raise(resp)
        return resp.json()

    def _post(self, path: str, json: object = None) -> Any:
        try:
            resp = httpx.post(f"{self._base}{path}", json=json, timeout=self._timeout)
        except httpx.TransportError as exc:
            raise ApiError(0, str(exc)) from exc
        _raise(resp)
        return None if resp.status_code == 204 else resp.json()

    def _delete(self, path: str) -> None:
        try:
            resp = httpx.delete(f"{self._base}{path}", timeout=self._timeout)
        except httpx.TransportError as exc:
            raise ApiError(0, str(exc)) from exc
        _raise(resp)

    # ── tags ─────────────────────────────────────────────────────────────────

    def get_tags(self) -> list[dict]:
        """Return [{tag: {id, name, slug, color}, count}, ...]."""
        return self._get("/api/tags")

    # ── books ─────────────────────────────────────────────────────────────────

    def get_books(self, tag_ids: list[int] | None = None) -> list[dict]:
        """Return list of book dicts, optionally filtered by tag IDs."""
        params: dict = {}
        if tag_ids:
            params["tags"] = tag_ids
        resp = httpx.get(f"{self._base}/api/books", params=params)
        _raise(resp)
        return resp.json()["items"]

    def get_book(self, book_id: int) -> dict:
        return self._get(f"/api/books/{book_id}")

    def attach_tag(self, book_id: int, tag_id: int) -> None:
        self._post(f"/api/books/{book_id}/tags", json={"tag_id": tag_id})

    def detach_tag(self, book_id: int, tag_id: int) -> None:
        self._delete(f"/api/books/{book_id}/tags/{tag_id}")

    # ── search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        mode: str = "semantic",
        tag_ids: list[int] | None = None,
        tag_mode: str = "all",
        k: int = 10,
    ) -> list[dict]:
        """Return flat list of hit dicts (book_id, page_start, snippet)."""
        params: dict = {"q": query, "mode": mode, "k": k, "tag_mode": tag_mode}
        if tag_ids:
            params["tags"] = tag_ids
        result = self._get("/api/search", params)
        return result.get("items", [])

    # ── reader ────────────────────────────────────────────────────────────────

    def get_page(self, book_id: int, page_no: int) -> str:
        """Return extracted text for one page."""
        result = self._get(f"/api/books/{book_id}/pages/{page_no}")
        return result["text"]

    # ── admin ─────────────────────────────────────────────────────────────────

    def scan(self) -> dict:
        return self._post("/api/admin/scan")


def _raise(resp: httpx.Response) -> None:
    if resp.is_error:
        try:
            msg = resp.json().get("detail", resp.text)
        except Exception:  # pylint: disable=broad-except
            msg = resp.text
        raise ApiError(resp.status_code, str(msg))
