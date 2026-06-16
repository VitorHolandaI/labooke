"""Retriever atual: chama /api/search via HTTP (mesmo que o CLI bible usa).

Serve como baseline para comparar com outras abordagens.
"""

from __future__ import annotations

import os

import httpx

from testes_arquitetura.base import Hit, Retriever

_DEFAULT_URL = os.getenv("LABOOKE_API_URL", "http://localhost:8000")


class SemanticApiRetriever(Retriever):
    """Busca semântica via HTTP API — comportamento atual do sistema."""

    def __init__(self, base_url: str = _DEFAULT_URL) -> None:
        self._base = base_url.rstrip("/")

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        resp = httpx.get(
            f"{self._base}/api/search",
            params={"q": query, "mode": "semantic", "k": k},
            timeout=120,
        )
        resp.raise_for_status()
        return [
            Hit(
                book_id=item["book_id"],
                page_start=item["page_start"],
                snippet=item["snippet"],
                score=item.get("score", 0.0),
            )
            for item in resp.json().get("items", [])
        ]


class LexicalApiRetriever(Retriever):
    """Busca lexical (título) via HTTP API."""

    def __init__(self, base_url: str = _DEFAULT_URL) -> None:
        self._base = base_url.rstrip("/")

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        resp = httpx.get(
            f"{self._base}/api/search",
            params={"q": query, "mode": "lexical", "k": k},
            timeout=30,
        )
        resp.raise_for_status()
        return [
            Hit(
                book_id=item["book_id"],
                page_start=item["page_start"],
                snippet=item["snippet"],
                score=item.get("score", 0.0),
            )
            for item in resp.json().get("items", [])
        ]
