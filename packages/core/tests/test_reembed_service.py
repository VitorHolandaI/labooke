
import numpy as np
from labooke_core.domain.models import BookStatus
from labooke_core.embed import chunk_pages
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.reembed_service import ReembedService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.db import open_db
from labooke_core.store.summaries_repo import SummariesRepo
from labooke_core.store.vectors_repo import VEC_DIM, VectorsRepo


class ConstantEncoder:
    def __call__(self, texts):
        rows = [[float(index + 1)] * VEC_DIM for index, _ in enumerate(texts)]
        return np.asarray(rows, dtype=np.float32)


def one_page_chunker(pages):
    return chunk_pages(pages, pages_per_chunk=1)


def two_page_chunker(pages):
    return chunk_pages(pages, pages_per_chunk=2)


def test_reembed_book_replaces_old_chunks_and_vectors(tmp_path):
    conn = open_db(":memory:", seed_tags=False)
    books = BooksRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    path = tmp_path / "sample.txt"
    lines = [f"line {index}" for index in range(1, 46)]
    path.write_text("\n".join(lines), encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt", page_count=1)
    old_chunk = chunks.insert(book_id=book.id, page_start=1, page_end=1)
    vectors.insert(chunk_id=old_chunk.id, vector=[0.1] * VEC_DIM)
    pipeline = BookEmbeddingPipeline(
        books,
        chunks,
        vectors,
        encode_texts=ConstantEncoder(),
        page_chunker=two_page_chunker,
    )
    service = ReembedService(books, pipeline)
    updated = service.reembed_book(book.id)
    assert updated.status is BookStatus.READY
    assert updated.page_count == 2
    new_chunks = chunks.list_for_book(book.id)
    assert [(chunk.page_start, chunk.page_end) for chunk in new_chunks] == [(1, 2)]
    assert conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0] == 1
    assert old_chunk.id != new_chunks[0].id


def test_reembed_book_updates_chunk_count_when_chunk_size_changes(tmp_path):
    conn = open_db(":memory:", seed_tags=False)
    books = BooksRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    path = tmp_path / "sample.txt"
    lines = [f"line {index}" for index in range(1, 46)]
    path.write_text("\n".join(lines), encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt", page_count=2)

    initial_pipeline = BookEmbeddingPipeline(
        books,
        chunks,
        vectors,
        encode_texts=ConstantEncoder(),
        page_chunker=one_page_chunker,
    )
    initial_pipeline.rebuild(book)
    assert [(chunk.page_start, chunk.page_end) for chunk in chunks.list_for_book(book.id)] == [
        (1, 1),
        (2, 2),
    ]

    changed_pipeline = BookEmbeddingPipeline(
        books,
        chunks,
        vectors,
        encode_texts=ConstantEncoder(),
        page_chunker=two_page_chunker,
    )
    updated = ReembedService(books, changed_pipeline).reembed_book(book.id)

    assert updated.status is BookStatus.READY
    assert updated.page_count == 2
    assert [(chunk.page_start, chunk.page_end) for chunk in chunks.list_for_book(book.id)] == [
        (1, 2)
    ]
    assert conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0] == 1


def test_reembed_refreshes_summary_vector_from_rag_text(tmp_path):
    conn = open_db(":memory:", seed_tags=False)
    books = BooksRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    summaries = SummariesRepo(conn)
    path = tmp_path / "sample.txt"
    path.write_text("line 1\nline 2\nline 3", encoding="utf-8")
    book = books.insert(sha256="a", path=path, title="Sample", format="txt")
    books.update_description(book.id, "readable summary")
    books.update_rag_text(book.id, "rag topics: A B C")
    pipeline = BookEmbeddingPipeline(
        books,
        chunks,
        vectors,
        encode_texts=ConstantEncoder(),
        page_chunker=one_page_chunker,
    )
    service = ReembedService(books, pipeline, summaries)
    service.reembed_book(book.id)
    assert [book_id for book_id, _ in summaries.knn(query=[2.0] * VEC_DIM, k=5)] == [book.id]


def test_reembed_uses_description_fallback_without_rag_text(tmp_path):
    conn = open_db(":memory:", seed_tags=False)
    books = BooksRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    summaries = SummariesRepo(conn)
    path = tmp_path / "sample.txt"
    path.write_text("line 1\nline 2\nline 3", encoding="utf-8")
    book = books.insert(sha256="b", path=path, title="Sample", format="txt")
    books.update_description(book.id, "fallback summary text")
    pipeline = BookEmbeddingPipeline(
        books,
        chunks,
        vectors,
        encode_texts=ConstantEncoder(),
        page_chunker=one_page_chunker,
    )
    ReembedService(books, pipeline, summaries).reembed_book(book.id)
    assert len(summaries.knn(query=[2.0] * VEC_DIM, k=5)) == 1
