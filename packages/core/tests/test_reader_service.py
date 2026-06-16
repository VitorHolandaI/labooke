
import pytest
from labooke_core.domain.models import PageText
from labooke_core.services.reader_service import ReaderService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def books(conn) -> BooksRepo:
    return BooksRepo(conn)


def test_get_page_reads_from_source_file(books, tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("first line\nsecond line", encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt")
    page = ReaderService(books).get_page(book.id, 1)
    assert page == PageText(page_no=1, text="first line\nsecond line")


def test_get_page_propagates_page_validation(books, tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("first line", encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt")
    with pytest.raises(ValueError, match="page_no=2 out of range"):
        ReaderService(books).get_page(book.id, 2)
