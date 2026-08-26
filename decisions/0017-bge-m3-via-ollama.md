# 0017 — BGE-M3 embeddings via a runtime-switchable Ollama endpoint

**Status:** accepted

## Context

The original in-process `multilingual-e5-small` integration fixed vectors at
384 dimensions and pulled PyTorch plus sentence-transformers into the API
container. The library needs stronger multilingual retrieval and may use a
more powerful Ollama host only while that GPU is available.

Qwen3 Embedding 4B was evaluated first. Its Ollama process used 4.3 GB total
memory with a CPU/GPU split and repeatedly terminated embedding requests with
an internal runner `EOF`. BGE-M3 returned normalized Portuguese embeddings
reliably on the same endpoint.

## Decision

- Use `bge-m3` through Ollama's native `/api/embed` endpoint.
- Store its native 1024-dimensional dense vectors in `vec_chunks` and
  `vec_summaries`.
- Keep hybrid passage retrieval as dense KNN + FTS5/BM25 fused with RRF.
- Remove sentence-transformers, PyTorch, the local model cache, and the idle
  subprocess worker from the API.
- Keep environment URLs as defaults. Admin may persist one Ollama root URL
  override; new embedding and chat calls resolve it immediately. Resetting the
  override restores the `.env` values.
- Migration 0009 recreates both vector tables empty. Re-embedding is never
  automatic; the operator starts it explicitly from Admin.

## Consequences

- Deployments need BGE-M3 installed on every selectable Ollama host.
- Changing the embedding model or dimensions requires another vector-table
  migration and a manual full re-embed.
- The API image and resident memory are smaller because inference is external.
- Search depends on Ollama during ingest, re-embed, and query encoding; stored
  metadata and reading remain available without it.

## Related

- [0003 — Search modes](0003-search-modes.md)
- [0007 — No hardcoded endpoints](0007-no-hardcoded-endpoints.md)
- [0015 — LLM descriptions and recommendations](0015-llm-summarize-ask.md)
- Docs: [search.md](../docs/search.md), [docker.md](../docs/docker.md)
