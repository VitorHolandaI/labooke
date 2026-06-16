"""Generate on-demand snippets for search hits."""

from __future__ import annotations

from collections.abc import Callable
from re import sub

from labooke_core.domain.models import SearchHit
from labooke_core.extract import Extractor, for_format
from labooke_core.store.books_repo import BooksRepo


def _compact_whitespace(text: str) -> str:
    return sub(r"\s+", " ", text).strip()


def _query_terms(query: str) -> list[str]:
    return [term.lower() for term in query.split() if term.strip()]


def _snippet_bounds(text: str, query: str) -> tuple[int, int]:
    normalized = text.lower()
    candidates = [normalized.find(term) for term in _query_terms(query)]
    positions = [pos for pos in candidates if pos >= 0]
    if not positions:
        return 0, min(len(text), 220)
    start = max(0, min(positions) - 80)
    end = min(len(text), min(positions) + 140)
    return start, end


class SnippetService:
    """Generate compact text snippets around a search query.

    Example:
        >>> type(SnippetService(None)).__name__
        'SnippetService'
    """

    def __init__(
        self,
        books: BooksRepo,
        *,
        extractor_factory: Callable[[str], Extractor] = for_format,
    ) -> None:
        self._books = books
        self._extractor_factory = extractor_factory

    def snippet_for_hit(self, hit: SearchHit, query: str) -> str:
        """Extract the hit page range and slice a snippet around ``query``.

        Example:
            >>> service = SnippetService(None)
            >>> service.snippet_for_hit.__name__
            'snippet_for_hit'
        """
        book = self._books.get(hit.book_id)
        extractor = self._extractor_factory(book.format)
        source = book.require_path()
        pages = [
            extractor.page_text(source, page_no)
            for page_no in range(hit.page_start, hit.page_end + 1)
        ]
        text = _compact_whitespace(" ".join(pages))
        start, end = _snippet_bounds(text, query)
        return text[start:end]
