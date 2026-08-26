"""Domain models shared across all labooke layers.

These are pure Pydantic types with no I/O, no SQL, and no framework
dependencies. Repositories and services map between these and storage
or HTTP shapes.
"""

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class BookStatus(StrEnum):
    """Lifecycle state of a book during and after ingest."""

    PENDING = "pending"
    READY = "ready"
    REEMBEDDING = "reembedding"
    FAILED = "failed"


class Tag(BaseModel):
    """A label applied to one or more books for filtering and organization.

    Example:
        >>> Tag(id=1, name="Linux", slug="linux", color="#22c55e")
        Tag(id=1, name='Linux', slug='linux', color='#22c55e')
    """

    id: int
    name: str
    slug: str
    color: str


class Book(BaseModel):
    """A book in the user's library.

    The on-disk file at ``path`` is the source of truth for text; the
    database stores only metadata, tags, and embedding chunks.
    """

    id: int
    sha256: str
    path: Path | None = None
    title: str
    author: str | None = None
    description: str | None = None
    format: str
    page_count: int = 0
    status: BookStatus = BookStatus.PENDING
    ingest_error: str | None = None
    tags: list[Tag] = Field(default_factory=list)

    def require_path(self) -> Path:
        """Return ``path`` or raise if the book has no source file.

        Reading text (extraction, snippets, paging) is impossible without
        a file on disk. Books can have a NULL path when their file went
        missing, so callers that need to read must go through here.

        Example:
            >>> book = Book(
            ...     id=1, sha256="x", path=Path("x.txt"), title="X", format="txt"
            ... )
            >>> book.require_path().name
            'x.txt'
        """
        if self.path is None:
            raise FileNotFoundError(
                f"book id={self.id} ({self.title!r}) has no source file on disk"
            )
        return self.path


class Chunk(BaseModel):
    """A contiguous page range of a book that maps 1:1 to one embedding."""

    id: int
    book_id: int
    page_start: int
    page_end: int
    text: str = ""


class PageText(BaseModel):
    """Extracted text for a single page; transient, never persisted."""

    page_no: int
    text: str


class SearchHit(BaseModel):
    """A single result from a semantic or lexical search query."""

    book_id: int
    page_start: int
    page_end: int
    snippet: str
    score: float


class Bookmark(BaseModel):
    """A user-saved pointer to a specific page within a book."""

    id: int
    book_id: int
    page_no: int
    label: str
    note: str | None = None


class ReadingProgress(BaseModel):
    """The last page the user read in a given book, with a timestamp."""

    book_id: int
    page_no: int
    updated_at: datetime
