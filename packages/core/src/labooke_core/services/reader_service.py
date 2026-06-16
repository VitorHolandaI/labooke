"""Direct page reads from the source book files."""

from __future__ import annotations

from collections.abc import Callable

from labooke_core.domain.models import PageText
from labooke_core.extract import Extractor, for_format
from labooke_core.store.books_repo import BooksRepo


class ReaderService:
    """Serve one logical page directly from the source book file.

    Example:
        >>> type(ReaderService(None)).__name__
        'ReaderService'
    """

    def __init__(
        self,
        books: BooksRepo,
        *,
        extractor_factory: Callable[[str], Extractor] = for_format,
    ) -> None:
        self._books = books
        self._extractor_factory = extractor_factory

    def get_page(self, book_id: int, page_no: int) -> PageText:
        """Return one 1-based logical page without reading text from the DB.

        Example:
            >>> service = ReaderService(None)
            >>> service.get_page.__name__
            'get_page'
        """
        book = self._books.get(book_id)
        extractor = self._extractor_factory(book.format)
        return PageText(page_no=page_no, text=extractor.page_text(book.require_path(), page_no))
