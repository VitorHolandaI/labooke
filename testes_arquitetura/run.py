"""Compara retrievers lado a lado para uma query.

Uso:
    python testes_arquitetura/run.py "design patterns"
    python testes_arquitetura/run.py "codigo orientado a objetos" --k 5
    python testes_arquitetura/run.py "concorrencia" --retriever hybrid
    python testes_arquitetura/run.py "concorrencia" --retriever all

Retrievers disponíveis: semantic, lexical, hybrid, cross_encoder, all
"""

from __future__ import annotations

import argparse
import textwrap
import time

from testes_arquitetura.base import Hit, Retriever
from testes_arquitetura.cross_encoder import CrossEncoderReranker
from testes_arquitetura.hybrid import HybridRRFRetriever
from testes_arquitetura.via_api import LexicalApiRetriever, SemanticApiRetriever

_RETRIEVERS: dict[str, Retriever] = {
    "semantic": SemanticApiRetriever(),
    "lexical": LexicalApiRetriever(),
    "hybrid": HybridRRFRetriever(),
    "cross_encoder": CrossEncoderReranker(),
}


def _print_hits(hits: list[Hit], elapsed: float) -> None:
    if not hits:
        print("  (sem resultados)")
        return
    for i, h in enumerate(hits, 1):
        snippet = textwrap.shorten(h.snippet, width=100, placeholder="…")
        print(f"  {i:2}. [livro {h.book_id}] p{h.page_start}  score={h.score:.4f}")
        print(f"      {snippet}")
    print(f"  ── {len(hits)} resultados em {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Query de busca")
    parser.add_argument("--k", type=int, default=5, help="Número de resultados")
    parser.add_argument(
        "--retriever",
        default="all",
        choices=[*_RETRIEVERS, "all"],
        help="Retriever a usar (padrão: all)",
    )
    args = parser.parse_args()

    targets = list(_RETRIEVERS.values()) if args.retriever == "all" else [_RETRIEVERS[args.retriever]]

    print(f'\nQuery: "{args.query}"  k={args.k}\n{"=" * 60}')
    for retriever in targets:
        print(f"\n[{retriever.name}]")
        t0 = time.monotonic()
        try:
            hits = retriever.search(args.query, k=args.k)
            elapsed = time.monotonic() - t0
            _print_hits(hits, elapsed)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERRO: {exc}")


if __name__ == "__main__":
    main()
