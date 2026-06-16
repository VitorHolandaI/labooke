"""Shared ingest/reembed book-to-chunks pipeline."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from labooke_core.domain.models import Book
from labooke_core.embed import TextChunk, chunk_pages
from labooke_core.embed import encode_passages as encode
from labooke_core.extract import Extractor, for_format
from labooke_core.store.books_repo import BooksRepo
from labooke_core.store.chunks_repo import ChunksRepo
from labooke_core.store.vectors_repo import VectorsRepo

EncodeFn = Callable[[Sequence[str]], np.ndarray]
ChunkerFn = Callable[..., list[TextChunk]]
ExtractorFactory = Callable[[str], Extractor]


class BookEmbeddingPipeline:
    """Rebuild chunks and embeddings for a stored book file.

    Example:
        >>> pipeline = BookEmbeddingPipeline(None, None, None)  # doctest: +ELLIPSIS
        >>> type(pipeline).__name__
        'BookEmbeddingPipeline'
    """

    def __init__(
        self,
        books: BooksRepo | None,
        chunks: ChunksRepo | None,
        vectors: VectorsRepo | None,
        *,
        encode_texts: EncodeFn = encode,
        page_chunker: ChunkerFn = chunk_pages,
        extractor_factory: ExtractorFactory = for_format,
    ) -> None:
        self._books = books
        self._chunks = chunks
        self._vectors = vectors
        self._encode_texts = encode_texts
        self._page_chunker = page_chunker
        self._extractor_factory = extractor_factory

    def rebuild(self, book: Book) -> int:
        """Replace persisted chunks/vectors from the current source file.

        Example:
            >>> pipeline = BookEmbeddingPipeline(None, None, None)
            >>> pipeline.rebuild.__name__
            'rebuild'

        Returns the logical page count extracted from ``book.path``.
        """
        extractor = self._extractor_factory(book.format)
        page_texts = list(extractor.pages(book.require_path()))
        text_chunks = self._page_chunker(page_texts)
        self._delete_existing_rows(book.id)
        inserted = self._insert_chunks(book.id, text_chunks)
        self._insert_vectors(inserted, text_chunks)
        return len(page_texts)

    def _delete_existing_rows(self, book_id: int) -> None:
        if self._chunks is None or self._vectors is None:
            return
        old_chunk_ids = [chunk.id for chunk in self._chunks.list_for_book(book_id)]
        self._vectors.delete_for_chunk_ids(old_chunk_ids)
        self._chunks.delete_for_book(book_id)

    def _insert_chunks(self, book_id: int, text_chunks: list[TextChunk]):
        if self._chunks is None:
            return []
        ranges = [(chunk.page_start, chunk.page_end, chunk.text) for chunk in text_chunks]
        return self._chunks.insert_many(book_id, ranges)

    def _insert_vectors(self, chunks, text_chunks: list[TextChunk]) -> None:
        if self._vectors is None or not chunks:
            return
        matrix = self._encode_texts([chunk.text for chunk in text_chunks])
        rows = [(chunk.id, vector) for chunk, vector in zip(chunks, matrix, strict=True)]
        self._vectors.insert_many(rows)
