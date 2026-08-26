"""Request and response schemas for book endpoints."""

from __future__ import annotations

from labooke_core.domain.models import Book
from pydantic import BaseModel, Field

from labooke_api.schemas.tags import TagOut


class BookOut(BaseModel):
    """JSON shape returned for a single book."""

    id: int
    sha256: str
    title: str
    author: str | None
    description: str | None
    format: str
    page_count: int
    status: str
    ingest_error: str | None
    tags: list[TagOut]

    @classmethod
    def from_domain(cls, book: Book) -> BookOut:
        """Map a domain :class:`Book` to the response schema."""
        return cls(
            id=book.id,
            sha256=book.sha256,
            title=book.title,
            author=book.author,
            description=book.description,
            format=book.format,
            page_count=book.page_count,
            status=book.status.value,
            ingest_error=book.ingest_error,
            tags=[TagOut.from_domain(tag) for tag in book.tags],
        )


class BookListOut(BaseModel):
    """List response wrapper for the library view."""

    items: list[BookOut]


class BookCreateResponse(BaseModel):
    """``202 Accepted`` payload returned from upload and scan ingest."""

    book_id: int
    status: str


class BookTagAttach(BaseModel):
    """Body for ``POST /api/books/{id}/tags``."""

    tag_id: int = Field(gt=0)


class BookUpdate(BaseModel):
    """Body for ``PATCH /api/books/{id}``.

    Only fields present in the request body are updated; an explicit
    ``null`` clears ``author`` or ``description``.
    """

    title: str | None = Field(default=None, min_length=1, max_length=500)
    author: str | None = None
    description: str | None = None
