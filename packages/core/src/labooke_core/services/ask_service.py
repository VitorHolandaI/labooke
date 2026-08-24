"""Ask-the-library: natural-language Q&A over book summaries (RAG)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from labooke_core.config import Settings
from labooke_core.domain.models import Book
from labooke_core.embed import encode_query
from labooke_core.llm import ChatClient, ChatMessage, LlmUnavailable
from labooke_core.services.library_service import LibraryService
from labooke_core.store.summaries_repo import SummariesRepo

_REFORMULATE_SYSTEM = (
    "You rewrite a user's natural-language library question into a short, "
    "keyword-style search query for semantic retrieval. Reply with only the "
    "query, no punctuation, no prose."
)

_ANSWER_SYSTEM = (
    "You are a librarian assistant for a personal book library. The user asks "
    "a question and you receive candidate books with summaries. Recommend the "
    "most relevant books and explain in one sentence why each fits. Answer in "
    "the same language as the user's question. If nothing fits, say so."
)


@dataclass(frozen=True, slots=True)
class AskAnswer:
    """The assistant's prose answer plus the candidate books it drew on."""

    answer: str
    books: list[Book]


def _format_candidates(books: Sequence[Book]) -> str:
    lines = []
    for index, book in enumerate(books, start=1):
        author = f" by {book.author}" if book.author else ""
        summary = book.description or "(no summary)"
        lines.append(f"{index}. {book.title}{author} — {summary}")
    return "\n".join(lines) if lines else "(no candidates)"


class AskService:
    """Answer library questions by retrieving summaries and asking the LLM.

    Pipeline (see the user-facing docs/ask.md):
    1. LLM reformulates the question into a search query.
    2. The query is embedded and KNN'd over ``vec_summaries``.
    3. The LLM reads only the top-K summaries and recommends books.

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
        chat_client: ChatClient | None = None,
        *,
        encode_texts: Callable[[Sequence[str]], np.ndarray] = encode_query,
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
        query = self._reformulate(client, question)
        candidate_ids = self._retrieve(query)
        books = [self._library.get_book(book_id) for book_id in candidate_ids]
        answer = self._answer(client, question, books)
        return AskAnswer(answer=answer, books=books)

    def _require_client(self) -> ChatClient:
        if self._chat_client is None:
            raise LlmUnavailable(
                "LLM not configured (set LABOOKE_LLM_BASE_URL and LABOOKE_LLM_MODEL)"
            )
        return self._chat_client

    def _reformulate(self, client: ChatClient, question: str) -> str:
        try:
            return client.chat(
                [
                    ChatMessage(role="system", content=_REFORMULATE_SYSTEM),
                    ChatMessage(role="user", content=question),
                ]
            ).strip()
        except LlmUnavailable:
            return question.strip()

    def _retrieve(self, query: str) -> list[int]:
        if not query:
            return []
        matrix = self._encode_texts([query])
        vector = [float(value) for value in matrix[0]]
        hits = self._summaries.knn(query=vector, k=self._settings.llm_rag_k)
        return [book_id for book_id, _ in hits]

    def _answer(self, client: ChatClient, question: str, books: Sequence[Book]) -> str:
        return client.chat(
            [
                ChatMessage(role="system", content=_ANSWER_SYSTEM),
                ChatMessage(
                    role="user",
                    content=f"Question: {question}\n\nCandidates:\n{_format_candidates(books)}",
                ),
            ]
        )
