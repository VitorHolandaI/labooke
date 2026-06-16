import pytest
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagNotFound, TagsRepo


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def tags(conn) -> TagsRepo:
    return TagsRepo(conn)


def make_book(books, sha="a"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=sha, format="pdf")


def test_merge_moves_links_from_source_to_target(books, tags):
    a, b, c = (make_book(books, sha=s) for s in ("a", "b", "c"))
    ml = tags.insert(name="ML", slug="ml")
    machine_learning = tags.insert(name="Machine Learning", slug="machine-learning")
    for bk in (a, b):
        tags.attach(bk.id, ml.id)
    tags.attach(c.id, machine_learning.id)

    tags.merge(source_id=ml.id, target_id=machine_learning.id)

    with pytest.raises(TagNotFound):
        tags.get(ml.id)
    for bk in (a, b, c):
        assert [t.slug for t in tags.for_book(bk.id)] == ["machine-learning"]


def test_merge_does_not_duplicate_when_book_has_both(books, tags):
    book = make_book(books)
    src = tags.insert(name="src", slug="src")
    tgt = tags.insert(name="tgt", slug="tgt")
    tags.attach(book.id, src.id)
    tags.attach(book.id, tgt.id)
    tags.merge(src.id, tgt.id)
    assert [t.slug for t in tags.for_book(book.id)] == ["tgt"]


def test_merge_into_self_raises(tags):
    t = tags.insert(name="x", slug="x")
    with pytest.raises(ValueError, match=r"merge tag id=.* into itself"):
        tags.merge(t.id, t.id)


def test_counts_returns_attached_book_count(books, tags):
    a, b = make_book(books, "a"), make_book(books, "b")
    linux = tags.insert(name="Linux", slug="linux")
    sec = tags.insert(name="Security", slug="security")
    tags.attach(a.id, linux.id)
    tags.attach(b.id, linux.id)
    tags.attach(a.id, sec.id)

    by_slug = {tag.slug: cnt for tag, cnt in tags.counts()}
    assert by_slug == {"linux": 2, "security": 1}


def test_counts_includes_tags_with_zero_books(tags):
    tags.insert(name="Unused", slug="unused")
    counts = tags.counts()
    assert counts == [(counts[0][0], 0)]
    assert counts[0][0].slug == "unused"


def test_counts_order_is_case_insensitive_by_name(tags):
    tags.insert(name="zebra", slug="z")
    tags.insert(name="alpha", slug="a")
    tags.insert(name="Beta", slug="b")
    names = [tag.name for tag, _ in tags.counts()]
    assert names == ["alpha", "Beta", "zebra"]
