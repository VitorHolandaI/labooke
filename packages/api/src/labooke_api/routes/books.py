"""HTTP routes for reading and mutating books."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from labooke_core.services import LibraryService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.tags_repo import TagsRepo

from labooke_api.deps import get_books_repo, get_library_service, get_tags_repo
from labooke_api.schemas import BookListOut, BookOut, BookTagAttach, BookUpdate

router = APIRouter(prefix="/api/books", tags=["books"])

BooksDep = Annotated[BooksRepo, Depends(get_books_repo)]
TagsDep = Annotated[TagsRepo, Depends(get_tags_repo)]
LibraryDep = Annotated[LibraryService, Depends(get_library_service)]


@router.get("", response_model=BookListOut)
def list_books(
    library: LibraryDep,
    tags: Annotated[Sequence[int], Query()] = (),
    tag_mode: Literal["all", "any"] = "all",
    exclude: Annotated[Sequence[int], Query()] = (),
    q: str | None = None,
) -> BookListOut:
    """List library books, filtered by tags and/or a lexical query."""
    books = library.list_books(tags=tags, tag_mode=tag_mode, exclude=exclude, q=q)
    return BookListOut(items=[BookOut.from_domain(book) for book in books])


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, library: LibraryDep) -> BookOut:
    """Return one book with its attached tags."""
    return BookOut.from_domain(library.get_book(book_id))


@router.patch("/{book_id}", response_model=BookOut)
def update_book(book_id: int, body: BookUpdate, library: LibraryDep) -> BookOut:
    """Rename a book and return it with attached tags."""
    return BookOut.from_domain(library.rename_book(book_id, body.title))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, books: BooksDep) -> None:
    """Delete a book row; cascades to chunks, vectors, bookmarks, progress."""
    books.get(book_id)
    books.delete(book_id)


@router.post("/{book_id}/tags", response_model=BookOut)
def attach_book_tag(
    book_id: int,
    body: BookTagAttach,
    books: BooksDep,
    tags: TagsDep,
    library: LibraryDep,
) -> BookOut:
    """Attach an existing tag to a book."""
    books.get(book_id)
    tags.get(body.tag_id)
    tags.attach(book_id, body.tag_id)
    return BookOut.from_domain(library.get_book(book_id))


@router.delete("/{book_id}/tags/{tag_id}", response_model=BookOut)
def detach_book_tag(
    book_id: int,
    tag_id: int,
    books: BooksDep,
    tags: TagsDep,
    library: LibraryDep,
) -> BookOut:
    """Remove a tag from a book."""
    books.get(book_id)
    tags.get(tag_id)
    tags.detach(book_id, tag_id)
    return BookOut.from_domain(library.get_book(book_id))
