"""Hybrid retriever: combina lexical + semântico e faz score fusion.

Estratégia: Reciprocal Rank Fusion (RRF).
  score_rrf = sum(1 / (k + rank_i))  para cada lista que contém o hit.

Vantagem sobre simplesmente juntar os dois: não precisa normalizar scores
de escalas diferentes (distância coseno vs. BM25).
"""

from __future__ import annotations

from collections import defaultdict

from testes_arquitetura.base import Hit, Retriever
from testes_arquitetura.via_api import LexicalApiRetriever, SemanticApiRetriever

_RRF_K = 60  # constante padrão do paper original (Cormack et al. 2009)


def _rrf_scores(hits_per_list: list[list[Hit]], *, k: int = _RRF_K) -> list[Hit]:
    scores: dict[tuple[int, int], float] = defaultdict(float)
    canonical: dict[tuple[int, int], Hit] = {}

    for ranked_list in hits_per_list:
        for rank, hit in enumerate(ranked_list, start=1):
            key = (hit.book_id, hit.page_start)
            scores[key] += 1.0 / (k + rank)
            canonical.setdefault(key, hit)

    return [
        Hit(
            book_id=key[0],
            page_start=key[1],
            snippet=canonical[key].snippet,
            score=round(score, 6),
        )
        for key, score in sorted(scores.items(), key=lambda x: -x[1])
    ]


class HybridRRFRetriever(Retriever):
    """Lexical + Semântico fundidos via Reciprocal Rank Fusion."""

    name = "HybridRRF (lexical + semântico)"

    def __init__(self, base_url: str | None = None) -> None:
        kwargs = {"base_url": base_url} if base_url else {}
        self._semantic = SemanticApiRetriever(**kwargs)
        self._lexical = LexicalApiRetriever(**kwargs)

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        semantic_hits = self._semantic.search(query, k=k * 2)
        lexical_hits = self._lexical.search(query, k=k * 2)
        fused = _rrf_scores([semantic_hits, lexical_hits])
        return fused[:k]
