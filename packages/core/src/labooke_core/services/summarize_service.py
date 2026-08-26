"""LLM-driven catalog descriptions from the opening pages."""

from __future__ import annotations

import itertools
import json
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from labooke_core.config import Settings
from labooke_core.domain.models import Book
from labooke_core.embed import encode_passages
from labooke_core.extract import Extractor, for_format
from labooke_core.llm import (
    ChatClient,
    ChatClientSource,
    ChatMessage,
    LlmUnavailable,
    resolve_chat_client,
)
from labooke_core.llm.json_response import extract_json_object
from labooke_core.prompts import catalog_description
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.summaries_repo import SummariesRepo

_MAX_EXCERPT_CHARS = 12_000


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """The LLM's readable catalog description and author guess."""

    summary: str
    author: str | None


def _parse_summary(text: str) -> SummaryResult:
    """Parse the LLM reply into a ``SummaryResult``.

    Falls back to treating the whole reply as the summary when the model
    does not return well-formed JSON (e.g. literal newlines inside a
    string or a trailing comma).
    """
    candidate = extract_json_object(text)
    try:
        payload = json.loads(candidate)
        summary = str(payload["summary"]).strip()
        author = payload.get("author")
        return SummaryResult(summary=summary, author=author or None)
    except (json.JSONDecodeError, KeyError, TypeError):
        return SummaryResult(summary=text.strip(), author=None)


class SummarizeService:
    """Read the first N pages and write one reusable catalog description.

    Example:
        >>> service = SummarizeService(None, None, None)
        >>> service.summarize.__name__
        'summarize'
    """

    def __init__(
        self,
        settings: Settings,
        books: BooksRepo,
        summaries: SummariesRepo,
        chat_client: ChatClientSource = None,
        *,
        pages_provider: Callable[[], int] | None = None,
        extractor_factory: Callable[[str], Extractor] = for_format,
        encode_texts: Callable[[Sequence[str]], np.ndarray] = encode_passages,
    ) -> None:
        self._settings = settings
        self._books = books
        self._summaries = summaries
        self._chat_client = chat_client
        self._pages_provider = pages_provider or (lambda: settings.llm_summary_pages)
        self._extractor_factory = extractor_factory
        self._encode_texts = encode_texts

    def summarize(self, book_id: int, *, pages: int | None = None) -> Book:
        """Generate and persist a catalog description for ``book_id``.

        ``pages`` overrides the configured page count for this call.

        Raises:
            LlmUnavailable: when no chat client is configured or the
                request fails.
        """
        client = self._require_client()
        book = self._books.get(book_id)
        page_limit = pages or self._pages_provider()
        excerpt = self._first_pages_text(book, page_limit)
        result = _parse_summary(self._generate(client, book, excerpt))
        self._books.update_description(book_id, result.summary)
        if result.author:
            self._books.update_author(book_id, result.author)
        self._store_summary_embedding(book_id, book.title, result.summary)
        return self._books.get(book_id)

    def summarize_many(
        self, book_ids: Sequence[int], pages: int | None = None
    ) -> list[tuple[int, str | None]]:
        """Summarize several books, one failure never stopping the batch.

        Returns ``(book_id, error_or_None)`` for each requested id.
        """
        results: list[tuple[int, str | None]] = []
        for book_id in book_ids:
            try:
                self.summarize(book_id, pages=pages)
                results.append((book_id, None))
            except Exception as exc:
                results.append((book_id, str(exc)))
        return results

    def pick_random_candidates(self, count: int) -> list[int]:
        """Return ``count`` random book ids that still lack a summary."""
        if count < 1:
            raise ValueError(f"count must be >= 1, got {count}")
        candidates = self._books.list_missing_description()
        if len(candidates) <= count:
            return [book.id for book in candidates]
        return [book.id for book in random.sample(candidates, count)]

    def invalidate_all(self) -> int:
        """Clear every book's description and catalog vector.

        Returns how many books had a summary cleared.
        """
        invalidated = 0
        for book in self._books.list_all():
            if not book.description:
                continue
            self._books.update_description(book.id, None)
            self._summaries.delete(book.id)
            invalidated += 1
        return invalidated

    def _require_client(self) -> ChatClient:
        client = resolve_chat_client(self._chat_client)
        if client is None:
            raise LlmUnavailable(
                "LLM not configured (set LABOOKE_LLM_BASE_URL and LABOOKE_LLM_MODEL)"
            )
        return client

    def _first_pages_text(self, book: Book, limit: int) -> str:
        extractor = self._extractor_factory(book.format)
        pages = (page.text for page in extractor.pages(book.require_path()))
        excerpt = "\n\n".join(
            page.strip() for page in itertools.islice(pages, limit) if page.strip()
        )
        return excerpt[:_MAX_EXCERPT_CHARS]

    def _generate(self, client: ChatClient, book: Book, excerpt: str) -> str:
        known_author = book.author or "unknown"
        return client.chat(
            [
                ChatMessage(role="system", content=catalog_description.SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=catalog_description.USER_PROMPT.format(
                        title=book.title,
                        author=known_author,
                        format=book.format,
                        excerpt=excerpt,
                    ),
                ),
            ]
        )

    def _store_summary_embedding(self, book_id: int, title: str, description: str) -> None:
        matrix = self._encode_texts([f"{title}\n{description}"])
        vector = [float(value) for value in matrix[0]]
        self._summaries.upsert(book_id=book_id, vector=vector)
