"""Request and response schemas for admin endpoints."""

from __future__ import annotations

from labooke_core.services import ScanResult
from pydantic import BaseModel, Field


class ScanResultOut(BaseModel):
    """JSON shape returned by ``POST /api/admin/scan``."""

    ingested: int
    skipped: int
    failed: int

    @classmethod
    def from_domain(cls, result: ScanResult) -> ScanResultOut:
        """Map a :class:`ScanResult` dataclass to the response schema."""
        return cls(
            ingested=result.ingested,
            skipped=result.skipped,
            failed=result.failed,
        )


class SummarizeRandomRequest(BaseModel):
    """Body for ``POST /api/admin/summaries/random``."""

    count: int = Field(ge=1, le=500)
    pages: int | None = Field(default=None, ge=1, le=5000)


class SummarizeBatchRequest(BaseModel):
    """Body for ``POST /api/admin/summaries/batch``."""

    book_ids: list[int] = Field(min_length=1)
    pages: int | None = Field(default=None, ge=1, le=5000)


class SummarizeBatchOut(BaseModel):
    """``202 Accepted`` payload listing the books scheduled for summary."""

    book_ids: list[int]


class InvalidateSummariesOut(BaseModel):
    """Payload returned after invalidating all book summaries."""

    invalidated: int


class AdminConfigUpdate(BaseModel):
    """Body for ``PUT /api/admin/config``.

    Only fields present in the request body are changed; a ``null``
    value resets a key back to the env-var default.
    """

    llm_summary_pages: int | None = Field(default=None, ge=1, le=5000)
