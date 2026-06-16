"""EPUB extraction via EbookLib and BeautifulSoup."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

from labooke_core.domain.models import PageText
from labooke_core.extract.base import PathLike, validate_page_range
from labooke_core.extract.common import load_image_bytes, save_webp, write_placeholder_cover


def _read_book(path: PathLike) -> epub.EpubBook:
    return epub.read_epub(str(Path(path)))


def _document_text(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text("\n", strip=True)
    return "\n".join(line for line in text.splitlines() if line.strip())


def _spine_item_ids(book: epub.EpubBook) -> list[str]:
    item_ids: list[str] = []
    for entry in book.spine:
        if isinstance(entry, tuple):
            item_ids.append(entry[0])
            continue
        item_ids.append(str(entry))
    return item_ids


def _ordered_document_texts(book: epub.EpubBook) -> list[str]:
    texts = [
        _document_text(book.get_item_with_id(item_id).get_content())
        for item_id in _spine_item_ids(book)
    ]
    pages = [text for text in texts if text]
    if pages:
        return pages
    return [_document_text(item.get_content()) for item in book.get_items_of_type(ITEM_DOCUMENT)]


def _cover_item(book: epub.EpubBook):
    for item in book.get_items():
        if type(item).__name__ == "EpubCover":
            return item
    return None


class EpubExtractor:
    """Extract chapter-like pages and cover thumbnails from EPUBs."""

    def pages(self, path: PathLike) -> Iterator[PageText]:
        """Yield one logical page per EPUB document item in reading order."""
        for page_no, text in enumerate(_ordered_document_texts(_read_book(path)), start=1):
            yield PageText(page_no=page_no, text=text)

    def page_text(self, path: PathLike, page_no: int) -> str:
        """Return extracted text for one 1-based EPUB page number."""
        texts = _ordered_document_texts(_read_book(path))
        validate_page_range(page_no, len(texts), path)
        return texts[page_no - 1]

    def page_count(self, path: PathLike) -> int:
        """Return the number of logical chapter/section pages in the EPUB."""
        return len(_ordered_document_texts(_read_book(path)))

    def write_cover_thumbnail(self, path: PathLike, destination: PathLike) -> Path:
        """Write the EPUB cover image as WEBP, or a placeholder when absent."""
        book = _read_book(path)
        cover = _cover_item(book)
        if cover is None:
            return write_placeholder_cover(destination, Path(path).stem)
        return save_webp(load_image_bytes(cover.get_content()), destination)
