# 0004 — Chunk size configurable via `CHUNK_PAGES`

**Status:** accepted

## Context

Each embedding represents N consecutive pages of a book. Smaller N gives
more precise hits but more vectors and bigger DB; larger N is the
opposite. Different users / corpora benefit from different choices.

## Decision

Expose `LABOOKE_CHUNK_PAGES` as an environment variable (default `1`).
One vector per page is the most precise setting and still tiny in
storage (≈30 vectors for a 300-page book at 1024-dim float32).

Changing the value affects only **new** ingests; existing books keep
their original chunking until re-embedded.

Trigger re-embedding via:

- `POST /api/books/{id}/reembed` — single book
- `POST /api/admin/reembed-all` — whole library (e.g. after a model swap)

Both run in the background; book status flips
`ready → reembedding → ready`.

## Consequences

- Users can trade precision for storage by changing one env var.
- Required "redo embeddings" buttons in the UI as a first-class feature
  (admin + per-book), not an afterthought.
- The same mechanism handles model swaps cleanly.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md) — re-embedding
  reads from the original file, no cached text needed.
- [0005 — Background ingest](0005-background-ingest.md) — re-embed reuses
  the ingest task runner and `BookStatus`.
- [0007 — Env vars](0007-no-hardcoded-endpoints.md) — `CHUNK_PAGES` is
  one of the `LABOOKE_*` settings.
