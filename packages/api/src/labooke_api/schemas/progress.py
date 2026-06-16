"""Request and response schemas for reading progress endpoints."""

from __future__ import annotations

from datetime import datetime

from labooke_core.domain.models import ReadingProgress
from pydantic import BaseModel, Field


class ProgressOut(BaseModel):
    """JSON shape for ``GET /api/books/{id}/progress``."""

    book_id: int
    page_no: int
    updated_at: datetime

    @classmethod
    def from_domain(cls, progress: ReadingProgress) -> ProgressOut:
        """Map a domain :class:`ReadingProgress` to the response schema."""
        return cls(
            book_id=progress.book_id,
            page_no=progress.page_no,
            updated_at=progress.updated_at,
        )


class ProgressUpdate(BaseModel):
    """Body for ``PUT /api/books/{id}/progress``."""

    page_no: int = Field(gt=0)
