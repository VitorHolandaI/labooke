"""PDF extraction via PyMuPDF."""

from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from labooke_core.domain.models import PageText
from labooke_core.extract.base import PathLike, validate_page_range
from labooke_core.extract.common import save_webp


def _open_document(path: PathLike) -> fitz.Document:
    return fitz.open(Path(path))


def _page_text(page: fitz.Page) -> str:
    return page.get_text("text").strip()


def _cover_image(page: fitz.Page) -> Image.Image:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return Image.open(BytesIO(pixmap.tobytes("png")))


class PdfExtractor:
    """Extract logical pages and cover thumbnails from PDFs."""

    def pages(self, path: PathLike) -> Iterator[PageText]:
        """Yield every PDF page as a 1-based :class:`PageText`.

        Example:
            >>> from labooke_core.extract import PdfExtractor
            >>> isinstance(PdfExtractor(), PdfExtractor)
            True
        """
        with _open_document(path) as document:
            for page_no, page in enumerate(document, start=1):
                yield PageText(page_no=page_no, text=_page_text(page))

    def page_text(self, path: PathLike, page_no: int) -> str:
        """Return extracted text for one 1-based PDF page number."""
        with _open_document(path) as document:
            validate_page_range(page_no, document.page_count, path)
            return _page_text(document.load_page(page_no - 1))

    def page_count(self, path: PathLike) -> int:
        """Return the number of pages in the PDF."""
        with _open_document(path) as document:
            return document.page_count

    def write_cover_thumbnail(self, path: PathLike, destination: PathLike) -> Path:
        """Render PDF page 1 into a WEBP cover thumbnail."""
        with _open_document(path) as document:
            if document.page_count < 1:
                raise ValueError(f"pdf at path={Path(path)!s} has no pages; expected >= 1")
            return save_webp(_cover_image(document.load_page(0)), destination)
