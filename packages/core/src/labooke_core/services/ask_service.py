"""Natural-language recommendations over generated book descriptions."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

from labooke_core.config import Settings
from labooke_core.domain.models import Book
from labooke_core.embed import encode_catalog_queries
from labooke_core.llm import (
    ChatClient,
    ChatClientSource,
    ChatMessage,
    LlmUnavailable,
    resolve_chat_client,
)
from labooke_core.llm.json_response import extract_json_object
from labooke_core.prompts import book_recommendation, catalog_query_expansion
from labooke_core.services.library_service import LibraryService
from labooke_core.store.summaries_repo import SummariesRepo


@dataclass(frozen=True, slots=True)
class AskAnswer:
    """The assistant's introduction, selected books, and per-book reasons."""

    answer: str
    books: list[Book]
    reasons: dict[int, str] = field(default_factory=dict)


def _format_candidates(books: Sequence[Book]) -> str:
    candidates = [
        {
            "book_id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description or "",
        }
        for book in books
    ]
    return json.dumps(candidates, ensure_ascii=False)


def _parse_queries(text: str, original: str) -> list[str]:
    """Return unique LLM search queries, falling back to the original request."""
    try:
        values = json.loads(extract_json_object(text))["queries"]
        if not isinstance(values, list):
            return [original]
        generated = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        return list(dict.fromkeys([original, *generated]))[:5]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [original]


def _parse_answer(text: str, candidates: Sequence[Book]) -> AskAnswer:
    fallback = AskAnswer(answer=text.strip(), books=list(candidates))
    try:
        payload = json.loads(extract_json_object(text))
        recommendations = payload["recommendations"]
        if not isinstance(recommendations, list):
            return fallback
        by_id = {book.id: book for book in candidates}
        selected: list[Book] = []
        reasons: dict[int, str] = {}
        for item in recommendations[:5]:
            book_id = int(item["book_id"])
            if book_id not in by_id or book_id in reasons:
                continue
            selected.append(by_id[book_id])
            reasons[book_id] = str(item.get("reason") or "").strip()
        return AskAnswer(
            answer=str(payload.get("message") or "").strip(),
            books=selected,
            reasons=reasons,
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return fallback


class AskService:
    """Recommend books by retrieving and reranking catalog descriptions.

    Pipeline (see the user-facing docs/ask.md):
    1. The LLM expands the natural request into semantic catalog queries.
    2. KNN over title + description vectors produces candidate books.
    3. The LLM reranks their full descriptions and explains each result.

    Example:
        >>> service = AskService(None, None, None)
        >>> service.ask.__name__
        'ask'
    """

    def __init__(
        self,
        settings: Settings,
        library: LibraryService,
        summaries: SummariesRepo,
        chat_client: ChatClientSource = None,
        *,
        encode_texts: Callable[[Sequence[str]], np.ndarray] = encode_catalog_queries,
    ) -> None:
        self._settings = settings
        self._library = library
        self._summaries = summaries
        self._chat_client = chat_client
        self._encode_texts = encode_texts

    def ask(self, question: str) -> AskAnswer:
        """Return a prose answer and the candidate books for ``question``.

        Raises:
            LlmUnavailable: when no chat client is configured or the
                request fails.
        """
        client = self._require_client()
        request = question.strip()
        queries = self._queries(client, request)
        candidate_ids = self._retrieve(queries)
        books = [self._library.get_book(book_id) for book_id in candidate_ids]
        return self._answer(client, request, books)

    def _require_client(self) -> ChatClient:
        client = resolve_chat_client(self._chat_client)
        if client is None:
            raise LlmUnavailable(
                "LLM not configured (set LABOOKE_LLM_BASE_URL and LABOOKE_LLM_MODEL)"
            )
        return client

    def _queries(self, client: ChatClient, request: str) -> list[str]:
        if not request:
            return []
        response = client.chat(
            [
                ChatMessage(role="system", content=catalog_query_expansion.SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=catalog_query_expansion.USER_PROMPT.format(request=request),
                ),
            ]
        )
        return _parse_queries(response, request)

    def _retrieve(self, queries: Sequence[str]) -> list[int]:
        if not queries:
            return []
        matrix = self._encode_texts(queries)
        scores: dict[int, float] = {}
        for vector in matrix:
            hits = self._summaries.knn(
                query=[float(value) for value in vector],
                k=self._settings.llm_rag_k,
            )
            for rank, (book_id, _) in enumerate(hits):
                scores[book_id] = scores.get(book_id, 0.0) + 1.0 / (60 + rank + 1)
        ranked = sorted(scores, key=lambda book_id: (-scores[book_id], book_id))
        return ranked[: self._settings.llm_rag_k]

    def _answer(self, client: ChatClient, question: str, books: Sequence[Book]) -> AskAnswer:
        response = client.chat(
            [
                ChatMessage(role="system", content=book_recommendation.SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=book_recommendation.USER_PROMPT.format(
                        request=question,
                        candidates=_format_candidates(books),
                    ),
                ),
            ]
        )
        return _parse_answer(response, books)
