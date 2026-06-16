"""Request and response schemas for bookmark endpoints."""

from __future__ import annotations

from labooke_core.domain.models import Bookmark
from pydantic import BaseModel, Field


class BookmarkOut(BaseModel):
    """JSON shape returned for a stored bookmark."""

    id: int
    book_id: int
    page_no: int
    label: str
    note: str | None

    @classmethod
    def from_domain(cls, bookmark: Bookmark) -> BookmarkOut:
        """Map a domain :class:`Bookmark` to the response schema."""
        return cls(
            id=bookmark.id,
            book_id=bookmark.book_id,
            page_no=bookmark.page_no,
            label=bookmark.label,
            note=bookmark.note,
        )


class BookmarkCreate(BaseModel):
    """Body for ``POST /api/books/{id}/bookmarks``."""

    page_no: int = Field(gt=0)
    label: str = Field(min_length=1)
    note: str | None = None


class BookmarkUpdateNote(BaseModel):
    """Body for ``PATCH /api/bookmarks/{id}``."""

    note: str | None = None
