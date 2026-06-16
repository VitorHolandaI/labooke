"""Response schemas for admin endpoints."""

from __future__ import annotations

from labooke_core.services import ScanResult
from pydantic import BaseModel


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
