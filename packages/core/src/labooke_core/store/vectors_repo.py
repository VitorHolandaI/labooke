"""Persistence for chunk embeddings via sqlite-vec.

The ``vec_chunks`` virtual table holds one row per chunk
(``chunk_id``, ``embedding FLOAT[384]``). This module hides the
serialization detail and exposes ``insert``, ``insert_many``,
``knn``, and deletion helpers.

KNN returns ``(chunk_id, distance)`` pairs ordered by ascending
distance (smaller = more similar). Services convert distance to a
similarity score appropriate for the chosen model.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection

VEC_DIM = 384  # intfloat/multilingual-e5-small (and most small sentence-transformers)


def _serialize(vector: Sequence[float]) -> bytes:
    """Pack a float vector into the layout sqlite-vec expects.

    Raises:
        ValueError: if the vector length does not match :data:`VEC_DIM`.
    """
    if len(vector) != VEC_DIM:
        raise ValueError(
            f"embedding has {len(vector)} dims, expected {VEC_DIM}"
        )
    return struct.pack(f"{VEC_DIM}f", *vector)


class VectorsRepo:
    """Store and search 384-dim chunk embeddings.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> conn = open_db(":memory:")
        >>> repo = VectorsRepo(conn)
        >>> repo.insert(chunk_id=1, vector=[0.1] * 384)
        >>> hits = repo.knn(query=[0.1] * 384, k=1)
        >>> [chunk_id for chunk_id, _ in hits]
        [1]
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def insert(self, *, chunk_id: int, vector: Sequence[float]) -> None:
        """Store one embedding linked to ``chunk_id``."""
        self._conn.execute(
            "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, _serialize(vector)),
        )
        self._conn.commit()

    def insert_many(self, items: Iterable[tuple[int, Sequence[float]]]) -> None:
        """Store multiple ``(chunk_id, vector)`` pairs in one transaction."""
        rows = [(cid, _serialize(vec)) for cid, vec in items]
        if not rows:
            return
        with self._conn:
            self._conn.executemany(
                "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
                rows,
            )

    def delete_for_chunk_ids(self, chunk_ids: Iterable[int]) -> None:
        """Remove vectors for the given chunk ids."""
        ids = list(chunk_ids)
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        self._conn.execute(
            f"DELETE FROM vec_chunks WHERE chunk_id IN ({placeholders})", ids
        )
        self._conn.commit()

    def knn(
        self,
        *,
        query: Sequence[float],
        k: int = 10,
        book_ids: Sequence[int] | None = None,
    ) -> list[tuple[int, float]]:
        """Return the top-``k`` nearest chunks to ``query``.

        Args:
            query: 384-dim embedding to search for.
            k: Number of hits to return. Must be >= 1.
            book_ids: Optional whitelist of books to restrict the
                search to (joins through the ``chunks`` table).

        Returns:
            List of ``(chunk_id, distance)`` tuples ordered by
            ascending distance.
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        blob = _serialize(query)
        if book_ids is None:
            sql = (
                "SELECT chunk_id, distance FROM vec_chunks "
                "WHERE embedding MATCH ? AND k = ? "
                "ORDER BY distance"
            )
            params: tuple = (blob, k)
        else:
            ids = list(book_ids)
            if not ids:
                return []
            placeholders = ",".join("?" * len(ids))
            sql = (
                "SELECT chunk_id, distance FROM vec_chunks "
                "WHERE embedding MATCH ? AND k = ? "
                f"AND chunk_id IN (SELECT id FROM chunks WHERE book_id IN ({placeholders})) "
                "ORDER BY distance"
            )
            params = (blob, k, *ids)
        rows = self._conn.execute(sql, params).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]
