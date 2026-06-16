"""Cross-encoder reranker sobre resultados semânticos.

Fluxo:
  1. Busca semântica retorna k*OVERSAMPLE candidatos
  2. Cross-encoder pontua cada par (query, snippet) diretamente
  3. Retorna top-k reordenados

Cross-encoders são mais lentos mas mais precisos: leem query+doc juntos
em vez de comparar vetores independentes.

Modelo padrão: cross-encoder/ms-marco-MiniLM-L-6-v2 (~85 MB)
  pip install sentence-transformers
"""

from __future__ import annotations

from testes_arquitetura.base import Hit, Retriever
from testes_arquitetura.via_api import SemanticApiRetriever

_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_OVERSAMPLE = 4  # busca k*4 candidates, rerank e corta em k


class CrossEncoderReranker(Retriever):
    """Rerank cross-encoder sobre candidatos semânticos."""

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        base_url: str | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = None  # lazy load
        kwargs = {"base_url": base_url} if base_url else {}
        self._semantic = SemanticApiRetriever(**kwargs)

    @property
    def name(self) -> str:
        return f"CrossEncoder ({self._model_name})"

    def _loaded_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name)
        return self._model

    def search(self, query: str, *, k: int = 10) -> list[Hit]:
        candidates = self._semantic.search(query, k=k * _OVERSAMPLE)
        if not candidates:
            return []

        pairs = [[query, hit.snippet] for hit in candidates]
        scores = self._loaded_model().predict(pairs)

        reranked = sorted(
            zip(candidates, scores),
            key=lambda x: -float(x[1]),
        )
        return [
            Hit(
                book_id=hit.book_id,
                page_start=hit.page_start,
                snippet=hit.snippet,
                score=round(float(score), 4),
            )
            for hit, score in reranked[:k]
        ]
