import sqlite3

import pytest
from labooke_core.domain.models import BookStatus
from labooke_core.store.books_repo import BookNotFound, BooksRepo
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagsRepo


@pytest.fixture
def conn():
    return open_db(":memory:", seed_tags=False)


@pytest.fixture
def repo(conn) -> BooksRepo:
    return BooksRepo(conn)


@pytest.fixture
def tags(conn) -> TagsRepo:
    return TagsRepo(conn)


def make_book(repo: BooksRepo, *, sha: str, title: str, path: str | None = None):
    return repo.insert(
        sha256=sha,
        path=path or f"/tmp/{sha}.pdf",
        title=title,
        format="pdf",
    )


def test_insert_returns_persisted_book(repo):
    book = repo.insert(sha256="abc", path="/tmp/x.pdf", title="X", format="pdf")
    assert book.id > 0
    assert book.title == "X"
    assert book.format == "pdf"
    assert book.status is BookStatus.PENDING
    assert book.page_count == 0
    assert book.author is None
    assert book.tags == []


def test_insert_persists_optional_fields(repo):
    book = repo.insert(
        sha256="def",
        path="/tmp/y.epub",
        title="Y",
        format="epub",
        author="Jane",
        page_count=42,
        status=BookStatus.READY,
    )
    fetched = repo.get(book.id)
    assert fetched.author == "Jane"
    assert fetched.page_count == 42
    assert fetched.status is BookStatus.READY


def test_get_raises_when_missing(repo):
    with pytest.raises(BookNotFound, match="no book with id=999"):
        repo.get(999)


def test_list_all_returns_books_ordered_by_id(repo):
    a = make_book(repo, sha="a", title="A")
    b = make_book(repo, sha="b", title="B")
    c = make_book(repo, sha="c", title="C")
    titles = [book.title for book in repo.list_all()]
    assert titles == ["A", "B", "C"]
    assert [book.id for book in repo.list_all()] == [a.id, b.id, c.id]


def test_list_all_returns_empty_list_on_fresh_db(repo):
    assert repo.list_all() == []


def test_delete_removes_book(repo):
    book = make_book(repo, sha="a", title="A")
    repo.delete(book.id)
    with pytest.raises(BookNotFound):
        repo.get(book.id)


def test_delete_is_noop_for_missing_id(repo):
    repo.delete(999)  # should not raise
    assert repo.list_all() == []


def test_unique_sha256_constraint(repo):
    make_book(repo, sha="dup", title="A")
    with pytest.raises(sqlite3.IntegrityError):
        make_book(repo, sha="dup", title="B", path="/tmp/b.pdf")


def test_get_by_sha256_returns_persisted_book(repo):
    inserted = make_book(repo, sha="abc123", title="Alpha")
    fetched = repo.get_by_sha256("abc123")
    assert fetched == inserted


def test_get_by_sha256_raises_when_missing(repo):
    with pytest.raises(BookNotFound, match="no book with sha256='missing'"):
        repo.get_by_sha256("missing")


def test_set_status_updates_status_and_error(repo):
    book = make_book(repo, sha="abc123", title="Alpha")
    updated = repo.set_status(
        book.id,
        status=BookStatus.FAILED,
        ingest_error="bad format",
    )
    assert updated.status is BookStatus.FAILED
    assert updated.ingest_error == "bad format"


def test_set_status_can_clear_ingest_error(repo):
    book = make_book(repo, sha="abc123", title="Alpha")
    repo.set_status(book.id, status=BookStatus.FAILED, ingest_error="bad format")
    updated = repo.set_status(book.id, status=BookStatus.READY, ingest_error=None)
    assert updated.status is BookStatus.READY
    assert updated.ingest_error is None


def test_set_status_can_update_page_count(repo):
    book = make_book(repo, sha="abc123", title="Alpha")
    updated = repo.set_status(book.id, status=BookStatus.READY, page_count=42)
    assert updated.page_count == 42


def test_update_title_changes_title(repo):
    book = make_book(repo, sha="title-1", title="Old")
    renamed = repo.update_title(book.id, "  New Title  ")
    assert renamed.title == "New Title"


def test_update_title_rejects_blank(repo):
    book = make_book(repo, sha="title-2", title="Keep")
    with pytest.raises(ValueError):
        repo.update_title(book.id, "   ")


def test_update_title_raises_when_missing(repo):
    from labooke_core.store.books_repo import BookNotFound

    with pytest.raises(BookNotFound):
        repo.update_title(9999, "X")


def test_insert_persists_description(repo):
    book = repo.insert(
        sha256="desc", path="/tmp/d.pdf", title="D", format="pdf", description="A summary"
    )
    assert repo.get(book.id).description == "A summary"


def test_update_author_sets_and_clears(repo):
    book = make_book(repo, sha="author", title="A")
    assert repo.update_author(book.id, "Jane").author == "Jane"
    assert repo.update_author(book.id, None).author is None


def test_update_description_sets_and_clears(repo):
    book = make_book(repo, sha="desc2", title="D")
    updated = repo.update_description(book.id, "About things")
    assert updated.description == "About things"
    assert repo.update_description(book.id, None).description is None


def test_find_returns_all_books_when_filters_are_empty(repo):
    a = make_book(repo, sha="a", title="A")
    b = make_book(repo, sha="b", title="B")
    assert repo.find() == [a, b]


def test_find_filters_by_all_tags(repo, tags):
    linux = tags.insert(name="Linux", slug="linux")
    security = tags.insert(name="Security", slug="security")
    only_linux = make_book(repo, sha="linux", title="Linux Basics")
    both = make_book(repo, sha="both", title="Hardening Linux")
    tags.attach(only_linux.id, linux.id)
    tags.attach(both.id, linux.id)
    tags.attach(both.id, security.id)
    found = repo.find(tags=[linux.id, security.id], tag_mode="all")
    assert [book.id for book in found] == [both.id]


def test_find_filters_by_any_tag(repo, tags):
    linux = tags.insert(name="Linux", slug="linux")
    security = tags.insert(name="Security", slug="security")
    linux_book = make_book(repo, sha="linux", title="Linux Basics")
    security_book = make_book(repo, sha="security", title="Threat Model")
    plain_book = make_book(repo, sha="plain", title="Cooking")
    tags.attach(linux_book.id, linux.id)
    tags.attach(security_book.id, security.id)
    found = repo.find(tags=[linux.id, security.id], tag_mode="any")
    assert [book.id for book in found] == [linux_book.id, security_book.id]
    assert plain_book.id not in [book.id for book in found]


def test_find_excludes_books_with_matching_tags(repo, tags):
    linux = tags.insert(name="Linux", slug="linux")
    excluded = make_book(repo, sha="linux", title="Linux Basics")
    kept = make_book(repo, sha="plain", title="Cooking")
    tags.attach(excluded.id, linux.id)
    found = repo.find(exclude=[linux.id])
    assert [book.id for book in found] == [kept.id]


def test_find_filters_by_title_and_filename_case_insensitive(repo):
    title_match = make_book(repo, sha="alpha", title="Linux Bible")
    path_match = make_book(
        repo,
        sha="beta",
        title="Reference",
        path="/tmp/Kernel-Guide.PDF",
    )
    make_book(repo, sha="gamma", title="Cooking")
    found = repo.find(q="linux")
    assert [book.id for book in found] == [title_match.id]
    filename_found = repo.find(q="kernel-guide")
    assert [book.id for book in filename_found] == [path_match.id]


def test_find_combines_lexical_and_tag_filters(repo, tags):
    linux = tags.insert(name="Linux", slug="linux")
    match = make_book(repo, sha="linux", title="Linux Admin")
    wrong_tag = make_book(repo, sha="plain", title="Linux Desktop")
    wrong_title = make_book(repo, sha="other", title="Python")
    tags.attach(match.id, linux.id)
    tags.attach(wrong_title.id, linux.id)
    found = repo.find(tags=[linux.id], q="admin")
    assert [book.id for book in found] == [match.id]
    assert wrong_tag.id not in [book.id for book in found]


def test_find_ignores_duplicate_tag_ids(repo, tags):
    linux = tags.insert(name="Linux", slug="linux")
    book = make_book(repo, sha="linux", title="Linux Admin")
    tags.attach(book.id, linux.id)
    found = repo.find(tags=[linux.id, linux.id], exclude=[linux.id, linux.id])
    assert found == []


def test_find_ignores_blank_query(repo):
    book = make_book(repo, sha="alpha", title="Alpha")
    assert repo.find(q="   ") == [book]


def test_find_rejects_unknown_tag_mode(repo):
    with pytest.raises(
        ValueError,
        match="invalid tag_mode='xor'; expected 'all' or 'any'",
    ):
        repo.find(tag_mode="xor")
