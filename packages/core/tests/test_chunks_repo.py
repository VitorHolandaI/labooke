import sqlite3

import pytest
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunkNotFound, ChunksRepo
from labooke_core.store.db import open_db


@pytest.fixture
def conn():
    return open_db(":memory:")


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def chunks(conn) -> ChunksRepo:
    return ChunksRepo(conn)


def make_book(books, sha="a"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=sha, format="pdf")


def test_insert_returns_chunk_with_id(books, chunks):
    book = make_book(books)
    chunk = chunks.insert(book_id=book.id, page_start=1, page_end=10)
    assert chunk.id > 0
    assert chunk.book_id == book.id
    assert chunk.page_start == 1
    assert chunk.page_end == 10


def test_insert_rejects_inverted_range(books, chunks):
    book = make_book(books)
    with pytest.raises(ValueError, match=r"page_end .* must be >= page_start"):
        chunks.insert(book_id=book.id, page_start=10, page_end=5)


def test_insert_rejects_non_positive_pages(books, chunks):
    book = make_book(books)
    with pytest.raises(ValueError, match="page numbers must be >= 1"):
        chunks.insert(book_id=book.id, page_start=0, page_end=5)


def test_insert_many_returns_chunks_in_order(books, chunks):
    book = make_book(books)
    ranges = [(1, 1, ""), (2, 2, ""), (3, 3, "")]
    inserted = chunks.insert_many(book.id, ranges)
    assert [(c.page_start, c.page_end) for c in inserted] == [(s, e) for s, e, _ in ranges]
    assert all(c.id > 0 for c in inserted)


def test_insert_many_empty_returns_empty(books, chunks):
    book = make_book(books)
    assert chunks.insert_many(book.id, []) == []


def test_get_raises_when_missing(chunks):
    with pytest.raises(ChunkNotFound, match="no chunk with id=99"):
        chunks.get(99)


def test_list_for_book_returns_in_page_order(books, chunks):
    book = make_book(books)
    chunks.insert(book_id=book.id, page_start=5, page_end=6)
    chunks.insert(book_id=book.id, page_start=1, page_end=2)
    chunks.insert(book_id=book.id, page_start=3, page_end=4)
    pages = [(c.page_start, c.page_end) for c in chunks.list_for_book(book.id)]
    assert pages == [(1, 2), (3, 4), (5, 6)]


def test_list_for_book_empty_returns_empty(books, chunks):
    book = make_book(books)
    assert chunks.list_for_book(book.id) == []


def test_delete_for_book_returns_count(books, chunks):
    book = make_book(books)
    chunks.insert_many(book.id, [(1, 1, ""), (2, 2, ""), (3, 3, "")])
    assert chunks.delete_for_book(book.id) == 3
    assert chunks.list_for_book(book.id) == []


def test_delete_for_book_returns_zero_when_no_chunks(books, chunks):
    book = make_book(books)
    assert chunks.delete_for_book(book.id) == 0


def test_unique_range_constraint(books, chunks):
    book = make_book(books)
    chunks.insert(book_id=book.id, page_start=1, page_end=5)
    with pytest.raises(sqlite3.IntegrityError):
        chunks.insert(book_id=book.id, page_start=1, page_end=5)


def test_deleting_book_cascades_chunks(books, chunks):
    book = make_book(books)
    chunks.insert(book_id=book.id, page_start=1, page_end=5)
    books.delete(book.id)
    assert chunks.list_for_book(book.id) == []
