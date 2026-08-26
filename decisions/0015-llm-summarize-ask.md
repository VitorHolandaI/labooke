# 0015 — LLM summarize + ask via thin OpenAI-compatible client

**Status:** accepted

## Context

Users want (1) an automatic book description/author filled from the opening
pages and (2) a natural-language "ask the library" that recommends books.
Passage search already has a separate chunk-level hybrid pipeline.

## Decision

- **Transport:** a thin `OpenAICompatibleClient` over stdlib `urllib`
  (`packages/core/src/labooke_core/llm/client.py`), talking to
  `/v1/chat/completions`. No LangChain — the research and the KISS rule
  agree a framework is overkill for these structured chat calls.
- **Config via env vars** (decision 0007): `LABOOKE_LLM_BASE_URL`,
  `LABOOKE_LLM_MODEL`, `LABOOKE_LLM_API_KEY`. Feature is **off** until
  both base URL and model are set; endpoints then return `503`.
  Ollama needs no key locally (the `api_key` field is ignored).
- **Summarize:** `SummarizeService` reads the first configured pages, asks
  for `{author, summary}`, writes `books.description`/`books.author`, and
  embeds `title + description` into `vec_summaries`.
- **Ask:** the LLM expands a request into catalog queries. Multi-query KNN
  over `vec_summaries` shortlists books; the LLM reranks their complete
  descriptions and returns only relevant books with reasons.
- **Separation:** content search remains hybrid KNN + BM25 over `chunks`.
  It does not call the LLM or use catalog descriptions.
- **Prompts:** each LLM responsibility owns a module under
  `labooke_core/prompts/`; services contain orchestration, not prompt prose.
- Summarize is **synchronous** (manual button); it does not reuse the
  ingest background machinery and does not touch `BookStatus`.

## Consequences

- Zero new Python runtime dependencies (stdlib HTTP + numpy already present).
- Swapping Ollama → OpenAI/LM Studio is an env change, no code.
- Recommendation quality is bounded by descriptions; books without one never
  appear in retrieval.
- Synchronous summarize can block the request for tens of seconds on
  slow models — acceptable at single-user scale; promotion to background
  is deferred.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md)
- [0007 — No hardcoded endpoints](0007-no-hardcoded-endpoints.md)
- [0009 — Hand-rolled migrations](0009-hand-rolled-migrations.md)
- Docs: [ask.md](../docs/ask.md), [database.md](../docs/database.md)
