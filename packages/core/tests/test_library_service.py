from pathlib import Path

import pytest
from labooke_core.services.library_service import LibraryService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.progress_repo import ProgressRepo
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


@pytest.fixture
def progress(conn) -> ProgressRepo:
    return ProgressRepo(conn)


@pytest.fixture
def library(books, tags) -> LibraryService:
    return LibraryService(books, tags)


def make_book(books: BooksRepo, tmp_path: Path, *, sha: str, title: str):
    path = tmp_path / f"{sha}.txt"
    path.write_text(title, encoding="utf-8")
    return books.insert(sha256=sha, path=path, title=title, format="txt")


def test_get_book_loads_attached_tags(books, tags, library, tmp_path):
    book = make_book(books, tmp_path, sha="a", title="Alpha")
    linux = tags.insert(name="Linux", slug="linux")
    tags.attach(book.id, linux.id)
    loaded = library.get_book(book.id)
    assert [tag.slug for tag in loaded.tags] == ["linux"]


def test_list_books_applies_filters_and_loads_tags(books, tags, library, tmp_path):
    linux = tags.insert(name="Linux", slug="linux")
    security = tags.insert(name="Security", slug="security")
    alpha = make_book(books, tmp_path, sha="a", title="Linux Admin")
    beta = make_book(books, tmp_path, sha="b", title="Threat Modeling")
    tags.attach(alpha.id, linux.id)
    tags.attach(beta.id, security.id)
    found = library.list_books(tags=[linux.id], q="admin")
    assert [book.id for book in found] == [alpha.id]
    assert [tag.slug for tag in found[0].tags] == ["linux"]


def test_update_author_loads_tags(books, tags, library, tmp_path):
    book = make_book(books, tmp_path, sha="a", title="Alpha")
    updated = library.update_author(book.id, "Jane")
    assert updated.author == "Jane"


def test_update_description_loads_tags(books, tags, library, tmp_path):
    book = make_book(books, tmp_path, sha="a", title="Alpha")
    updated = library.update_description(book.id, "About things")
    assert updated.description == "About things"


def test_recent_books_most_recent_first(books, tags, progress, tmp_path):
    library = LibraryService(books, tags, progress)
    first = make_book(books, tmp_path, sha="a", title="Alpha")
    second = make_book(books, tmp_path, sha="b", title="Beta")
    progress.set(book_id=first.id, page_no=1)
    progress.set(book_id=second.id, page_no=2)
    assert [book.id for book in library.recent_books()] == [second.id, first.id]


def test_recent_books_requires_progress(books, tags, library):
    with pytest.raises(RuntimeError, match="without a ProgressRepo"):
        library.recent_books()
