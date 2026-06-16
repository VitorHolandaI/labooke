"""Request and response schemas for tag endpoints."""

from __future__ import annotations

from labooke_core.domain.models import Tag
from pydantic import BaseModel, Field


class TagOut(BaseModel):
    """JSON shape returned for a single tag."""

    id: int
    name: str
    slug: str
    color: str

    @classmethod
    def from_domain(cls, tag: Tag) -> TagOut:
        """Map a domain :class:`Tag` to the response schema."""
        return cls(id=tag.id, name=tag.name, slug=tag.slug, color=tag.color)


class TagCountOut(BaseModel):
    """Tag plus the number of books currently attached."""

    tag: TagOut
    count: int


class TagCreate(BaseModel):
    """Body for ``POST /api/tags``."""

    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    color: str = Field(default="#888888")


class TagUpdate(BaseModel):
    """Body for ``PATCH /api/tags/{id}``."""

    name: str | None = None
    color: str | None = None


class TagMergeRequest(BaseModel):
    """Body for ``POST /api/tags/merge``."""

    source_id: int
    target_id: int
