"""Chunk extracted pages into embedding-sized text blocks."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import islice

from labooke_core.config import Settings
from labooke_core.domain.models import PageText


@dataclass(slots=True)
class TextChunk:
    """A page-range plus text payload ready for embedding.

    Example:
        >>> chunk = TextChunk(page_start=1, page_end=2, text="A\\n\\nB")
        >>> (chunk.page_start, chunk.page_end)
        (1, 2)
    """

    page_start: int
    page_end: int
    text: str


def _resolved_chunk_size(pages_per_chunk: int | None) -> int:
    if pages_per_chunk is None:
        return Settings().chunk_pages
    return pages_per_chunk


def _validate_chunk_size(pages_per_chunk: int) -> None:
    if pages_per_chunk < 1:
        raise ValueError(f"pages_per_chunk must be >= 1, got {pages_per_chunk}")


def _batched_pages(pages: Iterable[PageText], batch_size: int) -> Iterator[list[PageText]]:
    iterator = iter(pages)
    while batch := list(islice(iterator, batch_size)):
        yield batch


def _chunk_from_pages(pages: list[PageText]) -> TextChunk:
    return TextChunk(
        page_start=pages[0].page_no,
        page_end=pages[-1].page_no,
        text="\n\n".join(page.text for page in pages).strip(),
    )


def chunk_pages(
    pages: Iterable[PageText], *, pages_per_chunk: int | None = None
) -> list[TextChunk]:
    """Group extracted pages into embedding chunks.

    Example:
        >>> pages = [PageText(page_no=1, text='A'), PageText(page_no=2, text='B')]
        >>> [chunk.page_end for chunk in chunk_pages(pages, pages_per_chunk=1)]
        [1, 2]
    """
    size = _resolved_chunk_size(pages_per_chunk)
    _validate_chunk_size(size)
    return [_chunk_from_pages(batch) for batch in _batched_pages(pages, size)]
