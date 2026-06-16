"""Lexical and semantic library search."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np

from labooke_core.domain.models import Book, SearchHit
from labooke_core.embed import encode_query
from labooke_core.services.library_service import LibraryService
from labooke_core.services.snippet_service import SnippetService
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.vectors_repo import VectorsRepo

SearchMode = Literal["semantic", "lexical", "hybrid"]


def _rrf(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank + 1)


def _normalized_query(q: str) -> str:
    return q.strip()


def _lexical_score(book: Book, query: str) -> float:
    lowered = query.lower()
    if lowered in book.title.lower():
        return 2.0
    if book.path is not None and lowered in book.path.name.lower():
        return 1.0
    return 0.0


def _lexical_snippet(book: Book) -> str:
    if book.path is None or book.path.name == book.title:
        return book.title
    return f"{book.title} ({book.path.name})"


def _similarity(distance: float) -> float:
    return 1.0 / (1.0 + distance)


class SearchService:
    """Combine tag filters with lexical or semantic search modes.

    Example:
        >>> type(SearchService(None, None, None, None)).__name__
        'SearchService'
    """

    def __init__(
        self,
        library: LibraryService,
        chunks: ChunksRepo,
        vectors: VectorsRepo,
        snippets: SnippetService,
        books: BooksRepo | None = None,
        *,
        encode_texts=encode_query,
    ) -> None:
        self._library = library
        self._chunks = chunks
        self._vectors = vectors
        self._snippets = snippets
        self._books = books
        self._encode_texts = encode_texts

    def search(
        self,
        q: str,
        *,
        tags: Sequence[int] = (),
        tag_mode: str = "all",
        exclude: Sequence[int] = (),
        k: int = 10,
        mode: SearchMode = "semantic",
    ) -> list[SearchHit]:
        """Return ranked search hits for ``q`` under the chosen mode.

        Example:
            >>> service = SearchService(None, None, None, None)
            >>> service.search.__name__
            'search'
        """
        query = _normalized_query(q)
        if not query:
            return []
        if mode == "lexical":
            return self._lexical_hits(query, tags=tags, tag_mode=tag_mode, exclude=exclude)
        if mode == "semantic":
            return self._semantic_hits(query, tags=tags, tag_mode=tag_mode, exclude=exclude, k=k)
        if mode == "hybrid":
            return self._hybrid_hits(query, tags=tags, tag_mode=tag_mode, exclude=exclude, k=k)
        raise ValueError(f"unsupported mode={mode!r}")

    def _lexical_hits(
        self,
        query: str,
        *,
        tags: Sequence[int],
        tag_mode: str,
        exclude: Sequence[int],
    ) -> list[SearchHit]:
        books = self._library.list_books(tags=tags, tag_mode=tag_mode, exclude=exclude, q=query)
        ranked = sorted(books, key=lambda book: (-_lexical_score(book, query), book.id))
        return [
            SearchHit(
                book_id=book.id,
                page_start=1,
                page_end=max(1, book.page_count),
                snippet=_lexical_snippet(book),
                score=_lexical_score(book, query),
            )
            for book in ranked
        ]

    def _semantic_hits(
        self,
        query: str,
        *,
        tags: Sequence[int],
        tag_mode: str,
        exclude: Sequence[int],
        k: int,
    ) -> list[SearchHit]:
        books = self._library.list_books(tags=tags, tag_mode=tag_mode, exclude=exclude)
        if not books:
            return []
        query_matrix = self._encode_texts([query])
        query_vector = np.asarray(query_matrix[0], dtype=np.float32).tolist()
        hits = self._vectors.knn(
            query=query_vector,
            k=k,
            book_ids=[book.id for book in books],
        )
        return [self._semantic_hit(chunk_id, distance, query) for chunk_id, distance in hits]

    def _semantic_hit(self, chunk_id: int, distance: float, query: str) -> SearchHit:
        chunk = self._chunks.get(chunk_id)
        hit = SearchHit(
            book_id=chunk.book_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            snippet="",
            score=_similarity(distance),
        )
        return hit.model_copy(update={"snippet": self._snippets.snippet_for_hit(hit, query)})

    def _hybrid_hits(
        self,
        query: str,
        *,
        tags: Sequence[int],
        tag_mode: str,
        exclude: Sequence[int],
        k: int,
    ) -> list[SearchHit]:
        books = self._library.list_books(tags=tags, tag_mode=tag_mode, exclude=exclude)
        if not books:
            return []
        book_ids = [b.id for b in books]

        # Semantic ranking
        query_matrix = self._encode_texts([query])
        query_vector = np.asarray(query_matrix[0], dtype=np.float32).tolist()
        sem_hits = self._vectors.knn(query=query_vector, k=k, book_ids=book_ids)
        sem_book_rank: dict[int, int] = {}
        sem_chunk: dict[int, tuple[int, float]] = {}
        for rank, (chunk_id, distance) in enumerate(sem_hits):
            chunk = self._chunks.get(chunk_id)
            if chunk.book_id not in sem_book_rank:
                sem_book_rank[chunk.book_id] = rank
                sem_chunk[chunk.book_id] = (chunk_id, distance)

        # BM25 ranking via FTS5
        bm25_book_rank: dict[int, int] = {}
        if self._books is not None:
            fts_ids = self._books.search_fts(query, book_ids=book_ids)
            bm25_book_rank = {bid: rank for rank, bid in enumerate(fts_ids)}

        # RRF fusion: collect all candidate books
        all_book_ids = set(sem_book_rank) | set(bm25_book_rank)
        scored: list[tuple[float, int]] = []
        for bid in all_book_ids:
            score = _rrf(sem_book_rank.get(bid, k * 10)) + _rrf(bm25_book_rank.get(bid, k * 10))
            scored.append((score, bid))
        scored.sort(key=lambda x: -x[0])

        result: list[SearchHit] = []
        for rrf_score, bid in scored[:k]:
            if bid in sem_chunk:
                chunk_id, distance = sem_chunk[bid]
                hit = self._semantic_hit(chunk_id, distance, query)
                result.append(hit.model_copy(update={"score": rrf_score}))
            else:
                book = next(b for b in books if b.id == bid)
                result.append(SearchHit(
                    book_id=bid,
                    page_start=1,
                    page_end=max(1, book.page_count),
                    snippet=book.title,
                    score=rrf_score,
                ))
        return result
