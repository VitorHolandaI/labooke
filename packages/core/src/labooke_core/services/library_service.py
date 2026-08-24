"""Library listing and book hydration helpers."""

from __future__ import annotations

from collections.abc import Sequence

from labooke_core.domain.models import Book
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.progress_repo import ProgressRepo
from labooke_core.store.tags_repo import TagsRepo


class LibraryService:
    """Load books with their attached tags for list/detail views.

    Example:
        >>> type(LibraryService(None, None)).__name__
        'LibraryService'
    """

    def __init__(
        self,
        books: BooksRepo,
        tags: TagsRepo,
        progress: ProgressRepo | None = None,
    ) -> None:
        self._books = books
        self._tags = tags
        self._progress = progress

    def get_book(self, book_id: int) -> Book:
        """Return one book with its attached tags.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.get_book.__name__
            'get_book'
        """
        return self._with_tags(self._books.get(book_id))

    def list_books(
        self,
        *,
        tags: Sequence[int] = (),
        tag_mode: str = "all",
        exclude: Sequence[int] = (),
        q: str | None = None,
    ) -> list[Book]:
        """Return filtered books with attached tags.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.list_books.__name__
            'list_books'
        """
        books = self._books.find(tags=tags, tag_mode=tag_mode, exclude=exclude, q=q)
        return [self._with_tags(book) for book in books]

    def rename_book(self, book_id: int, title: str) -> Book:
        """Update a book's title and return it with attached tags.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.rename_book.__name__
            'rename_book'
        """
        return self._with_tags(self._books.update_title(book_id, title))

    def update_author(self, book_id: int, author: str | None) -> Book:
        """Set or clear a book's author and return it with tags.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.update_author.__name__
            'update_author'
        """
        return self._with_tags(self._books.update_author(book_id, author))

    def update_description(self, book_id: int, description: str | None) -> Book:
        """Set or clear a book's description and return it with tags.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.update_description.__name__
            'update_description'
        """
        return self._with_tags(self._books.update_description(book_id, description))

    def recent_books(self, *, limit: int = 50) -> list[Book]:
        """Return books with reading progress, most recently read first.

        Example:
            >>> service = LibraryService(None, None)
            >>> service.recent_books.__name__
            'recent_books'
        """
        if self._progress is None:
            raise RuntimeError("LibraryService was built without a ProgressRepo")
        entries = self._progress.recent(limit=limit)
        return [self._with_tags(self._books.get(entry.book_id)) for entry in entries]

    def _with_tags(self, book: Book) -> Book:
        return book.model_copy(update={"tags": self._tags.for_book(book.id)})
