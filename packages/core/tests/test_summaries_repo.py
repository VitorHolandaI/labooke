import pytest
from labooke_core.store.db import open_db
from labooke_core.store.summaries_repo import SummariesRepo
from labooke_core.store.vectors_repo import VEC_DIM


@pytest.fixture
def repo():
    return SummariesRepo(open_db(":memory:"))


def test_upsert_then_knn_returns_book(repo):
    repo.upsert(book_id=1, vector=[0.1] * VEC_DIM)
    hits = repo.knn(query=[0.1] * VEC_DIM, k=1)
    assert hits == [(1, 0.0)]


def test_upsert_replaces_existing_vector(repo):
    repo.upsert(book_id=1, vector=[0.1] * VEC_DIM)
    repo.upsert(book_id=1, vector=[0.9] * VEC_DIM)
    hits = repo.knn(query=[0.9] * VEC_DIM, k=1)
    assert [book_id for book_id, _ in hits] == [1]
    rows = repo._conn.execute("SELECT COUNT(*) FROM vec_summaries").fetchone()
    assert rows[0] == 1


def test_delete_removes_vector(repo):
    repo.upsert(book_id=1, vector=[0.1] * VEC_DIM)
    repo.delete(1)
    assert repo.knn(query=[0.1] * VEC_DIM, k=5) == []


def test_delete_is_noop_when_absent(repo):
    repo.delete(999)  # should not raise


def test_knn_rejects_k_below_one(repo):
    with pytest.raises(ValueError, match="k must be >= 1"):
        repo.knn(query=[0.1] * VEC_DIM, k=0)


def test_upsert_rejects_wrong_dimensions(repo):
    with pytest.raises(ValueError, match=f"expected {VEC_DIM}"):
        repo.upsert(book_id=1, vector=[0.1] * 10)
