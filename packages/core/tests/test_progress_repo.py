from datetime import datetime

import pytest
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.progress_repo import ProgressRepo


@pytest.fixture
def conn():
    return open_db(":memory:")


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def repo(conn) -> ProgressRepo:
    return ProgressRepo(conn)


def make_book(books, sha="a"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=sha, format="pdf")


def test_set_creates_row_on_first_call(books, repo):
    book = make_book(books)
    progress = repo.set(book_id=book.id, page_no=10)
    assert progress.book_id == book.id
    assert progress.page_no == 10
    assert isinstance(progress.updated_at, datetime)


def test_set_updates_existing_row(books, repo):
    book = make_book(books)
    repo.set(book_id=book.id, page_no=10)
    later = repo.set(book_id=book.id, page_no=42)
    assert later.page_no == 42
    # only one row total
    rows = repo._conn.execute("SELECT COUNT(*) FROM reading_progress").fetchone()
    assert rows[0] == 1


def test_set_rejects_page_zero(books, repo):
    book = make_book(books)
    with pytest.raises(ValueError, match="page_no must be >= 1"):
        repo.set(book_id=book.id, page_no=0)


def test_get_returns_none_when_unset(books, repo):
    book = make_book(books)
    assert repo.get(book.id) is None


def test_get_returns_persisted_progress(books, repo):
    book = make_book(books)
    repo.set(book_id=book.id, page_no=7)
    fetched = repo.get(book.id)
    assert fetched is not None
    assert fetched.page_no == 7


def test_clear_removes_progress(books, repo):
    book = make_book(books)
    repo.set(book_id=book.id, page_no=7)
    repo.clear(book.id)
    assert repo.get(book.id) is None


def test_clear_is_noop_when_unset(books, repo):
    book = make_book(books)
    repo.clear(book.id)  # should not raise


def test_book_delete_cascades_progress(books, repo):
    book = make_book(books)
    repo.set(book_id=book.id, page_no=7)
    books.delete(book.id)
    assert repo.get(book.id) is None
