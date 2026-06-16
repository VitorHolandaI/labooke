"""Shared extractor interfaces and validation helpers."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from labooke_core.domain.models import PageText

PathLike = Path | str


class Extractor(Protocol):
    """Interface for format-specific page and cover extraction.

    Example:
        >>> from labooke_core.extract import for_format
        >>> extractor = for_format("pdf")
        >>> type(extractor).__name__
        'PdfExtractor'
    """

    def pages(self, path: PathLike) -> Iterator[PageText]:
        """Yield every extracted page in reading order."""

    def page_text(self, path: PathLike, page_no: int) -> str:
        """Return the extracted text for one 1-based page number."""

    def page_count(self, path: PathLike) -> int:
        """Return the number of logical pages exposed by the extractor."""

    def write_cover_thumbnail(self, path: PathLike, destination: PathLike) -> Path:
        """Write a WEBP cover thumbnail and return its path."""


def validate_page_no(page_no: int) -> None:
    """Reject page numbers below the 1-based extractor contract."""
    if page_no < 1:
        raise ValueError(f"page_no must be >= 1, got {page_no}")


def validate_page_range(page_no: int, total_pages: int, path: PathLike) -> None:
    """Reject page numbers outside the extracted range for ``path``."""
    validate_page_no(page_no)
    if page_no > total_pages:
        raise ValueError(
            f"page_no={page_no} out of range for path={Path(path)!s}; expected 1..{total_pages}"
        )
