from pathlib import Path

import numpy as np
import pytest
from labooke_core.services.library_service import LibraryService
from labooke_core.services.search_service import SearchService
from labooke_core.services.snippet_service import SnippetService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import open_db
from labooke_core.store.tags_repo import TagsRepo
from labooke_core.store.vectors_repo import VEC_DIM, VectorsRepo


class KeywordEncoder:
    def __call__(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "beta" in lowered:
                vectors.append([0.9] * VEC_DIM)
            elif "alpha" in lowered:
                vectors.append([0.1] * VEC_DIM)
            else:
                vectors.append([0.5] * VEC_DIM)
        return np.asarray(vectors, dtype=np.float32)


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
def chunks(conn) -> ChunksRepo:
    return ChunksRepo(conn)


@pytest.fixture
def vectors(conn) -> VectorsRepo:
    return VectorsRepo(conn)


@pytest.fixture
def search(books, tags, chunks, vectors) -> SearchService:
    library = LibraryService(books, tags)
    snippets = SnippetService(books)
    return SearchService(library, chunks, vectors, snippets, encode_texts=KeywordEncoder())


def make_book(
    books: BooksRepo,
    tmp_path: Path,
    *,
    sha: str,
    title: str,
    filename: str,
    text: str,
):
    path = tmp_path / filename
    path.write_text(text, encoding="utf-8")
    return books.insert(sha256=sha, path=path, title=title, format="txt", page_count=1)


def test_lexical_search_matches_title_and_filename(books, tags, search, tmp_path):
    linux = tags.insert(name="Linux", slug="linux")
    title_book = make_book(
        books, tmp_path, sha="a", title="Linux Admin", filename="admin.txt", text="alpha"
    )
    file_book = make_book(
        books,
        tmp_path,
        sha="b",
        title="Reference",
        filename="kernel-guide.txt",
        text="beta",
    )
    tags.attach(title_book.id, linux.id)
    tags.attach(file_book.id, linux.id)
    hits = search.search("linux", tags=[linux.id], mode="lexical")
    assert [hit.book_id for hit in hits] == [title_book.id]
    hits = search.search("kernel-guide", tags=[linux.id], mode="lexical")
    assert [hit.book_id for hit in hits] == [file_book.id]


def test_semantic_search_combines_tag_filter_and_snippets(
    books, tags, chunks, vectors, search, tmp_path
):
    linux = tags.insert(name="Linux", slug="linux")
    sec = tags.insert(name="Security", slug="security")
    a_book = make_book(
        books,
        tmp_path,
        sha="a",
        title="Alpha",
        filename="alpha.txt",
        text="alpha topic\nbeta keyword appears here",
    )
    b_book = make_book(
        books,
        tmp_path,
        sha="b",
        title="Other",
        filename="other.txt",
        text="alpha only",
    )
    tags.attach(a_book.id, linux.id)
    tags.attach(b_book.id, sec.id)
    a_chunk = chunks.insert(book_id=a_book.id, page_start=1, page_end=1)
    b_chunk = chunks.insert(book_id=b_book.id, page_start=1, page_end=1)
    vectors.insert(chunk_id=a_chunk.id, vector=[0.9] * VEC_DIM)
    vectors.insert(chunk_id=b_chunk.id, vector=[0.1] * VEC_DIM)
    hits = search.search("beta", tags=[linux.id], mode="semantic", k=5)
    assert [hit.book_id for hit in hits] == [a_book.id]
    assert hits[0].page_start == 1
    assert "beta" in hits[0].snippet.lower()


def test_search_tag_filters_support_all_any_and_exclude(books, tags, search, tmp_path):
    linux = tags.insert(name="Linux", slug="linux")
    security = tags.insert(name="Security", slug="security")
    archived = tags.insert(name="Archived", slug="archived")
    linux_only = make_book(
        books,
        tmp_path,
        sha="a",
        title="Alpha Guide",
        filename="alpha.txt",
        text="alpha",
    )
    both = make_book(
        books,
        tmp_path,
        sha="b",
        title="Beta Guide",
        filename="beta.txt",
        text="alpha",
    )
    security_archived = make_book(
        books,
        tmp_path,
        sha="c",
        title="Gamma Guide",
        filename="gamma.txt",
        text="alpha",
    )
    linux_archived = make_book(
        books,
        tmp_path,
        sha="d",
        title="Delta Guide",
        filename="delta.txt",
        text="alpha",
    )
    tags.attach(linux_only.id, linux.id)
    tags.attach(both.id, linux.id)
    tags.attach(both.id, security.id)
    tags.attach(security_archived.id, security.id)
    tags.attach(security_archived.id, archived.id)
    tags.attach(linux_archived.id, linux.id)
    tags.attach(linux_archived.id, archived.id)

    all_hits = search.search("guide", tags=[linux.id, security.id], tag_mode="all", mode="lexical")
    assert [hit.book_id for hit in all_hits] == [both.id]

    any_hits = search.search("guide", tags=[linux.id, security.id], tag_mode="any", mode="lexical")
    assert [hit.book_id for hit in any_hits] == [
        linux_only.id,
        both.id,
        security_archived.id,
        linux_archived.id,
    ]

    exclude_hits = search.search(
        "guide",
        tags=[linux.id, security.id],
        tag_mode="any",
        exclude=[archived.id],
        mode="lexical",
    )
    assert [hit.book_id for hit in exclude_hits] == [linux_only.id, both.id]


def test_search_rejects_unknown_mode(search):
    with pytest.raises(ValueError, match="unsupported mode='bogus'"):
        search.search("linux", mode="bogus")
