"""Library listing and book hydration helpers."""

from __future__ import annotations

from collections.abc import Sequence

from labooke_core.domain.models import Book
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.tags_repo import TagsRepo


class LibraryService:
    """Load books with their attached tags for list/detail views.

    Example:
        >>> type(LibraryService(None, None)).__name__
        'LibraryService'
    """

    def __init__(self, books: BooksRepo, tags: TagsRepo) -> None:
        self._books = books
        self._tags = tags

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

    def _with_tags(self, book: Book) -> Book:
        return book.model_copy(update={"tags": self._tags.for_book(book.id)})
