import pytest
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagsRepo


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def tags(conn) -> TagsRepo:
    return TagsRepo(conn)


def make_book(books, sha="a", title="A"):
    return books.insert(sha256=sha, path=f"/tmp/{sha}.pdf", title=title, format="pdf")


def test_attach_links_tag_to_book(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    assert [t.slug for t in tags.for_book(book.id)] == ["linux"]


def test_attach_is_idempotent(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    tags.attach(book.id, linux.id)  # second call should not error
    assert len(tags.for_book(book.id)) == 1


def test_detach_removes_link(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    tags.detach(book.id, linux.id)
    assert tags.for_book(book.id) == []


def test_detach_is_noop_for_missing_link(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.detach(book.id, linux.id)  # never attached — should not raise


def test_for_book_returns_tags_sorted_by_name(books, tags):
    book = make_book(books)
    zebra = tags.insert(name="zebra", slug="zebra")
    alpha = tags.insert(name="alpha", slug="alpha")
    beta = tags.insert(name="Beta", slug="beta")
    for t in (zebra, alpha, beta):
        tags.attach(book.id, t.id)
    assert [t.name for t in tags.for_book(book.id)] == ["alpha", "Beta", "zebra"]


def test_for_book_empty_when_no_tags(books, tags):
    book = make_book(books)
    assert tags.for_book(book.id) == []


def test_deleting_book_cascades_book_tags(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    books.delete(book.id)
    # tag still exists, but no longer attached anywhere
    assert tags.get_by_slug("linux").id == linux.id
    assert tags.for_book(book.id) == []


def test_deleting_tag_cascades_book_tags(books, tags):
    book = make_book(books)
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    tags.delete(linux.id)
    assert tags.for_book(book.id) == []
