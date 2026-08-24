# 0015 — LLM summarize + ask via thin OpenAI-compatible client

**Status:** accepted

## Context

Users want (1) an automatic book summary/author filled from the opening
pages and (2) a natural-language "ask the library" that recommends books.
Both need an LLM. The user runs Ollama on a LAN host (`10.66.66.15`).

## Decision

- **Transport:** a thin `OpenAICompatibleClient` over stdlib `urllib`
  (`packages/core/src/labooke_core/llm/client.py`), talking to
  `/v1/chat/completions`. No LangChain — the research and the KISS rule
  agree a framework is overkill for two chat calls, and the project
  already wraps `sentence-transformers` itself.
- **Config via env vars** (decision 0007): `LABOOKE_LLM_BASE_URL`,
  `LABOOKE_LLM_MODEL`, `LABOOKE_LLM_API_KEY`. Feature is **off** until
  both base URL and model are set; endpoints then return `503`.
  Ollama needs no key locally (the `api_key` field is ignored).
- **Summarize:** `SummarizeService` reads the first
  `LABOOKE_LLM_SUMMARY_PAGES` pages, asks the LLM for `{author, summary}`,
  writes `books.description`/`books.author` (migration 0004), and embeds
  the summary into a new `vec_summaries` table (migration 0005).
- **Ask:** `AskService` is a RAG pipeline — LLM reformulates the question
  into a query, KNN over `vec_summaries` returns top-`LABOOKE_LLM_RAG_K`,
  then the LLM reads only those summaries and recommends books.
- Summarize is **synchronous** (manual button); it does not reuse the
  ingest background machinery and does not touch `BookStatus`.

## Consequences

- Zero new Python runtime dependencies (stdlib HTTP + numpy already present).
- Swapping Ollama → OpenAI/LM Studio is an env change, no code.
- Ask quality is bounded by the summaries; books without a summary never
  appear in retrieval.
- Synchronous summarize can block the request for tens of seconds on
  slow models — acceptable at single-user scale; promotion to background
  is deferred.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md)
- [0007 — No hardcoded endpoints](0007-no-hardcoded-endpoints.md)
- [0009 — Hand-rolled migrations](0009-hand-rolled-migrations.md)
- Docs: [ask.md](../docs/ask.md), [database.md](../docs/database.md)
