"""Persistence for book-summary embeddings via sqlite-vec.

One vector per book holds the embedding of its generated summary
(see ``SummarizeService``). ``AskService`` runs KNN over this table to
shortlist candidate books before handing those summaries to the LLM.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from labooke_core.store.vectors_repo import _serialize

if TYPE_CHECKING:
    from labooke_core.store.db import LockedConnection


class SummariesRepo:
    """Store and search one 384-dim summary embedding per book.

    Example:
        >>> from labooke_core.store.db import open_db
        >>> repo = SummariesRepo(open_db(":memory:"))
        >>> repo.upsert(book_id=1, vector=[0.1] * 384)
        >>> repo.knn(query=[0.1] * 384, k=1)
        [(1, 0.0)]
    """

    def __init__(self, conn: LockedConnection) -> None:
        self._conn = conn

    def upsert(self, *, book_id: int, vector: Sequence[float]) -> None:
        """Insert-or-replace the summary embedding for ``book_id``.

        sqlite-vec virtual tables do not support ``ON CONFLICT`` upsert,
        so this deletes any existing row before inserting.
        """
        blob = _serialize(vector)
        self._conn.execute("DELETE FROM vec_summaries WHERE book_id = ?", (book_id,))
        self._conn.execute(
            "INSERT INTO vec_summaries (book_id, embedding) VALUES (?, ?)",
            (book_id, blob),
        )
        self._conn.commit()

    def delete(self, book_id: int) -> None:
        """Remove the summary embedding for ``book_id``. No-op if absent."""
        self._conn.execute("DELETE FROM vec_summaries WHERE book_id = ?", (book_id,))
        self._conn.commit()

    def knn(self, *, query: Sequence[float], k: int = 10) -> list[tuple[int, float]]:
        """Return the top-``k`` books nearest to ``query`` by summary.

        Returns ``(book_id, distance)`` ordered by ascending distance.
        """
        if k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        blob = _serialize(query)
        rows = self._conn.execute(
            "SELECT book_id, distance FROM vec_summaries "
            "WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (blob, k),
        ).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]
