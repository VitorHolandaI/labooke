"""LLM-driven book summarization from the opening pages.

Each book gets two LLM-generated texts:
- ``description`` — a readable summary shown in the UI.
- ``rag_text`` — a keyword-rich retrieval-oriented text that is embedded
  into ``vec_summaries`` and used by ``AskService`` for semantic search.
"""

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
from labooke_core.llm import ChatClient, ChatMessage, LlmUnavailable
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.summaries_repo import SummariesRepo

_MAX_EXCERPT_CHARS = 12_000

_SUMMARIZE_SYSTEM = (
    "You catalog books for a personal library. Given the opening pages of a book, "
    "return a JSON object with exactly three keys: 'author' (the author's name as a "
    "string, or null if it cannot be determined), 'summary' (a 2-4 sentence readable "
    "summary of what the book is about, in the same language as the book), and "
    "'rag_summary' (a keyword-rich retrieval-oriented text of 3-5 sentences optimized "
    "for semantic search: list the main topics, concepts, techniques and terms of the "
    "book, in English if the book is technical). "
    "Respond with a single JSON object only — no markdown code fences, no prose."
)


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """The LLM's readable summary, RAG text, and author guess for a book."""

    summary: str
    rag_text: str | None
    author: str | None


def _extract_json_object(text: str) -> str:
    """Return the first ``{...}`` block in ``text``, ignoring markdown fences.

    Small open models frequently wrap their JSON reply in ```json fences
    or add trailing prose; this keeps ``_parse_summary`` robust to both.
    """
    cleaned = text.strip()
    for prefix in ("```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[: -len("```")].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def _parse_summary(text: str) -> SummaryResult:
    """Parse the LLM reply into a ``SummaryResult``.

    Falls back to treating the whole reply as the summary when the model
    does not return well-formed JSON (e.g. literal newlines inside a
    string or a trailing comma).
    """
    candidate = _extract_json_object(text)
    try:
        payload = json.loads(candidate)
        summary = str(payload["summary"]).strip()
        rag_text = payload.get("rag_summary")
        author = payload.get("author")
        return SummaryResult(
            summary=summary,
            rag_text=rag_text or None,
            author=author or None,
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return SummaryResult(summary=text.strip(), rag_text=None, author=None)


class SummarizeService:
    """Read the first N pages of a book and write both LLM texts.

    The readable summary goes to ``description``, the retrieval text to
    ``rag_text`` (embedded into ``vec_summaries`` for "ask" retrieval),
    and the author guess to ``author``.

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
        chat_client: ChatClient | None = None,
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
        """Generate and persist both texts for ``book_id``.

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
        if result.rag_text:
            self._books.update_rag_text(book_id, result.rag_text)
        if result.author:
            self._books.update_author(book_id, result.author)
        self._store_summary_embedding(book_id, result.rag_text or result.summary)
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
        """Clear every book's summary texts and summary vectors.

        Returns how many books had a summary cleared.
        """
        invalidated = 0
        for book in self._books.list_all():
            if not book.description:
                continue
            self._books.update_description(book.id, None)
            self._books.update_rag_text(book.id, None)
            self._summaries.delete(book.id)
            invalidated += 1
        return invalidated

    def _require_client(self) -> ChatClient:
        if self._chat_client is None:
            raise LlmUnavailable(
                "LLM not configured (set LABOOKE_LLM_BASE_URL and LABOOKE_LLM_MODEL)"
            )
        return self._chat_client

    def _first_pages_text(self, book: Book, limit: int) -> str:
        extractor = self._extractor_factory(book.format)
        pages = (page.text for page in extractor.pages(book.require_path()))
        excerpt = "\n\n".join(
            page.strip() for page in itertools.islice(pages, limit) if page.strip()
        )
        return excerpt[:_MAX_EXCERPT_CHARS]

    def _generate(self, client: ChatClient, book: Book, excerpt: str) -> str:
        return client.chat(
            [
                ChatMessage(role="system", content=_SUMMARIZE_SYSTEM),
                ChatMessage(role="user", content=f"Title: {book.title}\n\n{excerpt}"),
            ]
        )

    def _store_summary_embedding(self, book_id: int, text: str) -> None:
        matrix = self._encode_texts([text])
        vector = [float(value) for value in matrix[0]]
        self._summaries.upsert(book_id=book_id, vector=vector)