"""HTTP routes for bookmarks."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from labooke_core.store.bookmarks_repo import BookmarksRepo
from labooke_core.store.books_repo import BooksRepo

from labooke_api.deps import get_bookmarks_repo, get_books_repo
from labooke_api.schemas import BookmarkCreate, BookmarkOut, BookmarkUpdateNote

router = APIRouter(tags=["bookmarks"])

BooksDep = Annotated[BooksRepo, Depends(get_books_repo)]
BookmarksDep = Annotated[BookmarksRepo, Depends(get_bookmarks_repo)]


@router.get("/api/books/{book_id}/bookmarks", response_model=list[BookmarkOut])
def list_bookmarks(
    book_id: int, books: BooksDep, bookmarks: BookmarksDep
) -> list[BookmarkOut]:
    """Return every bookmark stored for ``book_id`` ordered by page."""
    books.get(book_id)
    return [BookmarkOut.from_domain(bm) for bm in bookmarks.list_for_book(book_id)]


@router.post(
    "/api/books/{book_id}/bookmarks",
    response_model=BookmarkOut,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    book_id: int,
    body: BookmarkCreate,
    books: BooksDep,
    bookmarks: BookmarksDep,
) -> BookmarkOut:
    """Create a bookmark on a book page."""
    books.get(book_id)
    bookmark = bookmarks.insert(
        book_id=book_id, page_no=body.page_no, label=body.label, note=body.note
    )
    return BookmarkOut.from_domain(bookmark)


@router.patch("/api/bookmarks/{bookmark_id}", response_model=BookmarkOut)
def update_bookmark_note(
    bookmark_id: int, body: BookmarkUpdateNote, bookmarks: BookmarksDep
) -> BookmarkOut:
    """Replace the note on a bookmark."""
    bookmarks.get(bookmark_id)
    return BookmarkOut.from_domain(bookmarks.update_note(bookmark_id, body.note))


@router.delete("/api/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(bookmark_id: int, bookmarks: BookmarksDep) -> None:
    """Delete a bookmark."""
    bookmarks.get(bookmark_id)
    bookmarks.delete(bookmark_id)
