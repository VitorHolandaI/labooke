"""Schema for the page-text reader endpoint."""

from __future__ import annotations

from labooke_core.domain.models import PageText
from pydantic import BaseModel


class PageTextOut(BaseModel):
    """JSON shape for ``GET /api/books/{id}/pages/{n}``."""

    page_no: int
    text: str

    @classmethod
    def from_domain(cls, page: PageText) -> PageTextOut:
        """Map a domain :class:`PageText` to the response schema."""
        return cls(page_no=page.page_no, text=page.text)
