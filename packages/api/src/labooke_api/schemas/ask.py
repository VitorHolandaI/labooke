"""Request and response schemas for the ask-the-library endpoint."""

from __future__ import annotations

from labooke_core.domain.models import Book
from pydantic import BaseModel, Field

from labooke_api.schemas.books import BookOut


class AskRequest(BaseModel):
    """Body for ``POST /api/ask``."""

    question: str = Field(min_length=1, max_length=1000)


class AskResponse(BaseModel):
    """Prose answer plus the candidate books the LLM drew on."""

    answer: str
    books: list[BookOut]

    @classmethod
    def from_domain(cls, answer: str, books: list[Book]) -> AskResponse:
        """Map an ``AskAnswer`` to the response schema."""
        return cls(answer=answer, books=[BookOut.from_domain(book) for book in books])
