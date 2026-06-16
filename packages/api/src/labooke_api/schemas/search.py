"""Response schemas for search endpoints."""

from __future__ import annotations

from labooke_core.domain.models import SearchHit
from pydantic import BaseModel


class SearchHitOut(BaseModel):
    """JSON shape for a single search hit."""

    book_id: int
    page_start: int
    page_end: int
    snippet: str
    score: float

    @classmethod
    def from_domain(cls, hit: SearchHit) -> SearchHitOut:
        """Map a domain :class:`SearchHit` to the response schema."""
        return cls(
            book_id=hit.book_id,
            page_start=hit.page_start,
            page_end=hit.page_end,
            snippet=hit.snippet,
            score=hit.score,
        )


class SearchGroupOut(BaseModel):
    """Hits grouped under their owning book."""

    book_id: int
    hits: list[SearchHitOut]


class SearchResponse(BaseModel):
    """Response wrapper for both flat and grouped search results."""

    items: list[SearchHitOut] = []
    groups: list[SearchGroupOut] = []
    grouped: bool = False
