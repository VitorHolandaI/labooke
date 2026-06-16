"""Plain-text and Markdown extraction."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from labooke_core.domain.models import PageText
from labooke_core.extract.base import PathLike, validate_page_range
from labooke_core.extract.common import write_placeholder_cover

LINES_PER_PAGE = 40


def _read_text(path: PathLike) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _chunk_lines(lines: list[str]) -> list[str]:
    if not lines:
        return [""]
    return [
        "\n".join(lines[index : index + LINES_PER_PAGE]).strip()
        for index in range(0, len(lines), LINES_PER_PAGE)
    ]


def _pages(path: PathLike) -> list[str]:
    return _chunk_lines(_read_text(path).splitlines())


class TextExtractor:
    """Extract logical pages from TXT and Markdown files."""

    def pages(self, path: PathLike) -> Iterator[PageText]:
        """Yield fixed-size line chunks as 1-based logical pages."""
        for page_no, text in enumerate(_pages(path), start=1):
            yield PageText(page_no=page_no, text=text)

    def page_text(self, path: PathLike, page_no: int) -> str:
        """Return extracted text for one 1-based text page number."""
        texts = _pages(path)
        validate_page_range(page_no, len(texts), path)
        return texts[page_no - 1]

    def page_count(self, path: PathLike) -> int:
        """Return the number of fixed-size logical pages in the text file."""
        return len(_pages(path))

    def write_cover_thumbnail(self, path: PathLike, destination: PathLike) -> Path:
        """Write a placeholder WEBP cover derived from the file name."""
        return write_placeholder_cover(destination, Path(path).stem)
