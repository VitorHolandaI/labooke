import pytest
from labooke_core.store.bookmarks_repo import BookmarkNotFound, BookmarksRepo
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db


@pytest.fixture
def conn():
    return open_db(":memory:")


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def repo(conn) -> BookmarksRepo:
    return BookmarksRepo(conn)


def make_book(books, sha="a"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=sha, format="pdf")


def test_insert_returns_bookmark(books, repo):
    book = make_book(books)
    bm = repo.insert(book_id=book.id, page_no=10, label="chapter 1")
    assert bm.id > 0
    assert bm.book_id == book.id
    assert bm.page_no == 10
    assert bm.label == "chapter 1"
    assert bm.note is None


def test_insert_with_note(books, repo):
    book = make_book(books)
    bm = repo.insert(book_id=book.id, page_no=5, label="here", note="reread")
    assert bm.note == "reread"


def test_insert_rejects_page_zero(books, repo):
    book = make_book(books)
    with pytest.raises(ValueError, match="page_no must be >= 1"):
        repo.insert(book_id=book.id, page_no=0, label="x")


def test_get_raises_when_missing(repo):
    with pytest.raises(BookmarkNotFound, match="no bookmark with id=42"):
        repo.get(42)


def test_list_for_book_orders_by_page(books, repo):
    book = make_book(books)
    repo.insert(book_id=book.id, page_no=50, label="late")
    repo.insert(book_id=book.id, page_no=10, label="early")
    repo.insert(book_id=book.id, page_no=20, label="mid")
    pages = [bm.page_no for bm in repo.list_for_book(book.id)]
    assert pages == [10, 20, 50]


def test_list_for_book_empty(books, repo):
    book = make_book(books)
    assert repo.list_for_book(book.id) == []


def test_update_note_replaces_value(books, repo):
    book = make_book(books)
    bm = repo.insert(book_id=book.id, page_no=1, label="x", note="old")
    updated = repo.update_note(bm.id, "new")
    assert updated.note == "new"


def test_update_note_can_clear(books, repo):
    book = make_book(books)
    bm = repo.insert(book_id=book.id, page_no=1, label="x", note="something")
    updated = repo.update_note(bm.id, None)
    assert updated.note is None


def test_delete_removes_bookmark(books, repo):
    book = make_book(books)
    bm = repo.insert(book_id=book.id, page_no=1, label="x")
    repo.delete(bm.id)
    with pytest.raises(BookmarkNotFound):
        repo.get(bm.id)


def test_delete_noop_for_missing(repo):
    repo.delete(999)  # should not raise


def test_book_delete_cascades(books, repo):
    book = make_book(books)
    repo.insert(book_id=book.id, page_no=1, label="x")
    books.delete(book.id)
    assert repo.list_for_book(book.id) == []
