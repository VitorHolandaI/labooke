"""LLM-assisted classification using only the library's existing tags."""

from __future__ import annotations

import json
from collections.abc import Sequence

from labooke_core.domain.models import Tag
from labooke_core.llm import (
    ChatClient,
    ChatClientSource,
    ChatMessage,
    LlmUnavailable,
    resolve_chat_client,
)
from labooke_core.llm.json_response import extract_json_object
from labooke_core.prompts import book_auto_tag
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.tags_repo import TagsRepo


class AutoTagService:
    """Attach LLM-selected existing tags to summarized books.

    Example:
        >>> service = AutoTagService(None, None)
        >>> service.tag_book.__name__
        'tag_book'
    """

    def __init__(
        self,
        books: BooksRepo,
        tags: TagsRepo,
        chat_client: ChatClientSource = None,
    ) -> None:
        self._books = books
        self._tags = tags
        self._chat_client = chat_client

    def tag_book(self, book_id: int) -> list[Tag]:
        """Classify ``book_id`` and attach valid existing tags."""
        client = self._require_client()
        book = self._books.get(book_id)
        if not book.description:
            raise ValueError(
                f"book id={book_id} has description={book.description!r}; expected non-empty text"
            )
        available = self._tags.list_all()
        if not available:
            return []
        selected = self._select(client, book.title, book.description, available)
        for tag_id in selected:
            self._tags.attach(book_id, tag_id)
        return self._tags.for_book(book_id)

    def tag_many(self, book_ids: Sequence[int]) -> list[tuple[int, str | None]]:
        """Auto-tag books independently so one failure does not stop the batch."""
        results: list[tuple[int, str | None]] = []
        for book_id in book_ids:
            try:
                self.tag_book(book_id)
                results.append((book_id, None))
            except Exception as exc:
                results.append((book_id, str(exc)))
        return results

    def _require_client(self) -> ChatClient:
        client = resolve_chat_client(self._chat_client)
        if client is None:
            raise LlmUnavailable(
                "LLM not configured (set LABOOKE_LLM_BASE_URL and LABOOKE_LLM_MODEL)"
            )
        return client

    def _select(
        self,
        client: ChatClient,
        title: str,
        description: str,
        available: Sequence[Tag],
    ) -> list[int]:
        allowed = {tag.id for tag in available}
        tags_json = json.dumps(
            [{"id": tag.id, "name": tag.name} for tag in available],
            ensure_ascii=False,
        )
        reply = client.chat(
            [
                ChatMessage(role="system", content=book_auto_tag.SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=book_auto_tag.USER_PROMPT.format(
                        title=title,
                        description=description[:2_000],
                        tags=tags_json,
                    ),
                ),
            ]
        )
        try:
            values = json.loads(extract_json_object(reply))["tag_ids"]
            if not isinstance(values, list):
                return []
            selected = [value for value in values if isinstance(value, int) and value in allowed]
            return list(dict.fromkeys(selected))[:5]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return []
