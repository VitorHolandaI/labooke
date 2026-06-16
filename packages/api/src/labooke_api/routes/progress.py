"""HTTP routes for reading progress."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.progress_repo import ProgressRepo

from labooke_api.deps import get_books_repo, get_progress_repo
from labooke_api.schemas import ProgressOut, ProgressUpdate

router = APIRouter(prefix="/api/books/{book_id}/progress", tags=["progress"])

BooksDep = Annotated[BooksRepo, Depends(get_books_repo)]
ProgressDep = Annotated[ProgressRepo, Depends(get_progress_repo)]


@router.get("", response_model=ProgressOut)
def get_progress(
    book_id: int, books: BooksDep, progress: ProgressDep
) -> ProgressOut:
    """Return reading progress for ``book_id``; 404 if none recorded yet."""
    books.get(book_id)
    current = progress.get(book_id)
    if current is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "progress_not_found", "message": f"no progress for book_id={book_id}"},
        )
    return ProgressOut.from_domain(current)


@router.put("", response_model=ProgressOut)
def set_progress(
    book_id: int,
    body: ProgressUpdate,
    books: BooksDep,
    progress: ProgressDep,
) -> ProgressOut:
    """Upsert the user's last-read page."""
    books.get(book_id)
    return ProgressOut.from_domain(progress.set(book_id=book_id, page_no=body.page_no))
