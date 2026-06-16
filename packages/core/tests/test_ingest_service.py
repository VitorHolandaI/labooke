from pathlib import Path

import numpy as np
from labooke_core.config import Settings
from labooke_core.domain.models import BookStatus
from labooke_core.services._book_embedding_pipeline import BookEmbeddingPipeline
from labooke_core.services.ingest_service import IngestService
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
            else:
                vectors.append([0.1] * VEC_DIM)
        return np.asarray(vectors, dtype=np.float32)


def build_services(tmp_path: Path):
    settings = Settings(data_dir=tmp_path / "data", import_dir=tmp_path / "inbox")
    conn = open_db(settings.db_path, seed_tags=False)
    books = BooksRepo(conn)
    tags = TagsRepo(conn)
    chunks = ChunksRepo(conn)
    vectors = VectorsRepo(conn)
    library = LibraryService(books, tags)
    pipeline = BookEmbeddingPipeline(books, chunks, vectors, encode_texts=KeywordEncoder())
    ingest = IngestService(settings, books, tags, library, pipeline)
    search = SearchService(
        library,
        chunks,
        vectors,
        SnippetService(books),
        encode_texts=KeywordEncoder(),
    )
    return settings, books, tags, chunks, vectors, library, ingest, search


def test_ingest_round_trip_populates_search(tmp_path):
    settings, _books, tags, chunks, vectors, _library, ingest, search = build_services(tmp_path)
    source = tmp_path / "source.txt"
    lines = [f"alpha line {index}" for index in range(1, 41)]
    lines.extend(f"beta line {index}" for index in range(41, 46))
    source.write_text("\n".join(lines), encoding="utf-8")
    topic = tags.insert(name="Topic", slug="topic")
    book = ingest.ingest_book(source, tags=[topic.id])
    assert book.status is BookStatus.READY
    assert book.page_count == 2
    assert book.path.parent == settings.books_dir
    assert chunks.list_for_book(book.id)
    assert vectors.knn(query=[0.9] * VEC_DIM, k=5)
    hits = search.search("beta", tags=[topic.id], mode="semantic", k=1)
    assert [hit.book_id for hit in hits] == [book.id]
    assert (hits[0].page_start, hits[0].page_end) == (2, 2)
    assert "beta" in hits[0].snippet.lower()


def test_ingest_dedup_merges_tags_without_new_book(tmp_path):
    _settings, books, tags, _chunks, _vectors, library, ingest, _search = build_services(
        tmp_path
    )
    source = tmp_path / "source.txt"
    source.write_text("alpha page", encoding="utf-8")
    linux = tags.insert(name="Linux", slug="linux")
    security = tags.insert(name="Security", slug="security")
    first = ingest.ingest_book(source, tags=[linux.id])
    second = ingest.ingest_book(source, tags=[security.id])
    assert first.id == second.id
    assert len(books.list_all()) == 1
    assert {tag.slug for tag in library.get_book(first.id).tags} == {"linux", "security"}
