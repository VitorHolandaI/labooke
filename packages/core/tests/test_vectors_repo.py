import pytest
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import open_db
from labooke_core.store.vectors_repo import VEC_DIM, VectorsRepo


@pytest.fixture
def conn():
    return open_db(":memory:")


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def chunks(conn) -> ChunksRepo:
    return ChunksRepo(conn)


@pytest.fixture
def vectors(conn) -> VectorsRepo:
    return VectorsRepo(conn)


def make_book(books, sha="a"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=sha, format="pdf")


def make_chunk(books, chunks, sha="a", pages=(1, 1)):
    book = make_book(books, sha=sha)
    return book, chunks.insert(book_id=book.id, page_start=pages[0], page_end=pages[1])


def vec(value: float):
    return [value] * VEC_DIM


def test_insert_then_knn_finds_chunk(books, chunks, vectors):
    _, chunk = make_chunk(books, chunks)
    vectors.insert(chunk_id=chunk.id, vector=vec(0.1))
    hits = vectors.knn(query=vec(0.1), k=1)
    assert hits == [(chunk.id, pytest.approx(0.0, abs=1e-4))]


def test_insert_rejects_wrong_dimension(books, chunks, vectors):
    _, chunk = make_chunk(books, chunks)
    with pytest.raises(ValueError, match="expected 384"):
        vectors.insert(chunk_id=chunk.id, vector=[0.1] * 100)


def test_knn_orders_by_distance(books, chunks, vectors):
    _, near = make_chunk(books, chunks, sha="n", pages=(1, 1))
    _, far = make_chunk(books, chunks, sha="f", pages=(1, 1))
    vectors.insert(chunk_id=near.id, vector=vec(0.10))
    vectors.insert(chunk_id=far.id, vector=vec(0.90))
    hits = vectors.knn(query=vec(0.11), k=2)
    assert [cid for cid, _ in hits] == [near.id, far.id]


def test_knn_respects_k(books, chunks, vectors):
    for i in range(5):
        _, ck = make_chunk(books, chunks, sha=str(i), pages=(1, 1))
        vectors.insert(chunk_id=ck.id, vector=vec(i * 0.1))
    assert len(vectors.knn(query=vec(0.0), k=3)) == 3


def test_knn_rejects_k_zero(vectors):
    with pytest.raises(ValueError, match="k must be >= 1"):
        vectors.knn(query=vec(0.0), k=0)


def test_knn_book_filter_narrows_results(books, chunks, vectors):
    a_book, a_chunk = make_chunk(books, chunks, sha="a", pages=(1, 1))
    _b_book, b_chunk = make_chunk(books, chunks, sha="b", pages=(1, 1))
    vectors.insert(chunk_id=a_chunk.id, vector=vec(0.1))
    vectors.insert(chunk_id=b_chunk.id, vector=vec(0.1))
    hits = vectors.knn(query=vec(0.1), k=10, book_ids=[a_book.id])
    assert [cid for cid, _ in hits] == [a_chunk.id]


def test_knn_empty_book_ids_returns_empty(books, chunks, vectors):
    _, chunk = make_chunk(books, chunks)
    vectors.insert(chunk_id=chunk.id, vector=vec(0.1))
    assert vectors.knn(query=vec(0.1), k=5, book_ids=[]) == []


def test_insert_many_persists_all(books, chunks, vectors):
    items = []
    for i in range(3):
        _, ck = make_chunk(books, chunks, sha=str(i), pages=(1, 1))
        items.append((ck.id, vec(i * 0.1)))
    vectors.insert_many(items)
    hits = vectors.knn(query=vec(0.0), k=3)
    assert {cid for cid, _ in hits} == {cid for cid, _ in items}


def test_insert_many_empty_is_noop(vectors):
    vectors.insert_many([])  # should not raise


def test_delete_for_chunk_ids_removes_vectors(books, chunks, vectors):
    _, chunk = make_chunk(books, chunks)
    vectors.insert(chunk_id=chunk.id, vector=vec(0.1))
    vectors.delete_for_chunk_ids([chunk.id])
    assert vectors.knn(query=vec(0.1), k=5) == []


def test_delete_for_chunk_ids_empty_is_noop(vectors):
    vectors.delete_for_chunk_ids([])  # should not raise
