"""Request and response schemas for the ask-the-library endpoint."""

from __future__ import annotations

from labooke_core.services.ask_service import AskAnswer
from pydantic import BaseModel, Field

from labooke_api.schemas.books import BookOut


class AskRequest(BaseModel):
    """Body for ``POST /api/ask``."""

    question: str = Field(min_length=1, max_length=1000)


class AskRecommendationOut(BaseModel):
    """A selected book and the model's grounded relevance reason."""

    book: BookOut
    reason: str


class AskResponse(BaseModel):
    """Recommendation introduction plus selected books and reasons."""

    answer: str
    books: list[BookOut]
    recommendations: list[AskRecommendationOut]

    @classmethod
    def from_domain(cls, result: AskAnswer) -> AskResponse:
        """Map an ``AskAnswer`` to the response schema."""
        return cls(
            answer=result.answer,
            books=[BookOut.from_domain(book) for book in result.books],
            recommendations=[
                AskRecommendationOut(
                    book=BookOut.from_domain(book),
                    reason=result.reasons.get(book.id, ""),
                )
                for book in result.books
            ],
        )
