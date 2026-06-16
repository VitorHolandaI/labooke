# 0005 — Ingest runs in background; book status polled

**Status:** accepted

## Context

Embedding a 300-page PDF on CPU takes ~5–15s. Blocking the HTTP request
forces the user to sit on the upload page watching a spinner.

## Decision

Upload returns immediately:

1. `POST /api/books` saves the file, computes sha256, inserts a row with
   `status='pending'`, schedules a background task, and returns
   `202 {book_id, status: 'pending'}`.
2. Background task extracts → chunks → embeds → flips status to
   `ready` (or `failed` with `ingest_error`).
3. Frontend renders the book card immediately with a spinner overlay and
   polls `GET /api/books/{id}` until status changes.

Implementation: FastAPI `BackgroundTasks` for v1. Promotion to Celery/RQ
deferred until something forces it.

## Consequences

- Upload UI feels instant.
- Polling is wasteful but cheap at single-user scale; WebSocket push is
  on the v2 deferred list.
- A second `BookStatus` value, `reembedding`, reuses the same machinery
  for the redo-embeddings flow.
- Failed ingests stay in the library with the error message visible.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md) — only chunks +
  embeddings are written during ingest.
- [0004 — `CHUNK_PAGES`](0004-chunk-pages-env-var.md) — the reembed flow
  uses this same background machinery.
- [0006 — sha256 dedup](0006-sha256-dedup.md) — runs before the
  background task is scheduled.
