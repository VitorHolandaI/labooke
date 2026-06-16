
from labooke_core.domain.models import SearchHit
from labooke_core.services.snippet_service import SnippetService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.db import open_db


def test_snippet_for_hit_contains_query_context(tmp_path):
    conn = open_db(":memory:", seed_tags=False)
    books = BooksRepo(conn)
    path = tmp_path / "sample.txt"
    lines = [f"line {index}" for index in range(1, 60)]
    lines[44] = "the search needle appears here"
    path.write_text("\n".join(lines), encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt")
    hit = SearchHit(book_id=book.id, page_start=1, page_end=2, snippet="", score=1.0)
    snippet = SnippetService(books).snippet_for_hit(hit, "needle")
    assert "needle" in snippet
    assert len(snippet) < 220
