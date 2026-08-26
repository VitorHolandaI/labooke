# labooke — Design (1 page)

**Goal.** Local, low-RAM book library + reader for PDF/EPUB/TXT/MD,
with tag organization and semantic search. Lighter than Booklore
(~250MB standby vs ~700MB).

**Stack.** Python 3.12 + FastAPI + Pydantic v2 + sqlite-vec +
BGE-M3 embeddings served by Ollama; React +
Vite + TypeScript + CSS Modules + TanStack Query on the frontend; uv
workspace; Docker compose; Gitea Actions CI. A companion CLI `bible`
(post-web) shares the `core` lib directly — no HTTP.

**Domain.** `Book` (id, sha256, path, title, format, status, tags),
`Tag`, `Chunk` (page range), `Bookmark`, `ReadingProgress`,
`SearchHit`. All Pydantic; no framework deps in the domain layer.

**Storage.** Original file = source of truth for text. DB stores only
metadata, tags, chunk page-ranges, and embeddings. Snippets are
extracted on demand. Schema evolves via numbered SQL migrations.
See [decision 0001](decisions/0001-storage-no-text-in-db.md).

**Tags.** Flat (no hierarchy v1). Domain exposes `book.tags: list[Tag]`;
storage uses a hidden junction table for fast multi-tag AND/OR
filtering. See [decision 0002](decisions/0002-tags-flat-with-junction-table.md).

**Search.** Three orthogonal modes, all combinable in one query:
1. tag filter (SQL, no semantics)
2. lexical (title/filename `LIKE`)
3. semantic (vector KNN, scoped to the tag-filtered subset)

Response is flat hits with optional `?group_by_book=true`. See
[decision 0003](decisions/0003-search-modes.md).

**Ingest.** Two paths, both reuse `IngestService` and sha256 dedup:
- HTTP upload (`POST /api/books`, returns 202, background task)
- Folder scan of `LABOOKE_IMPORT_DIR` via `POST /api/admin/scan`

Status transitions: `pending → ready | failed`. Re-embed runs the
same pipeline. See [decisions 0005](decisions/0005-background-ingest.md),
[0006](decisions/0006-sha256-dedup.md),
[0014](decisions/0014-folder-scan-ingest.md).

**Config.** Every host/port/path comes from `LABOOKE_*` env vars
(backend) or `VITE_*` (frontend). No literals in source. Vite dev
proxies `/api/*` to the API (no CORS).

**More:** [TODO.md](TODO.md) for the work plan,
[decisions/README.md](decisions/README.md) for full ADRs,
[SESSION.md](SESSION.md) for current status.
