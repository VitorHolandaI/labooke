# labooke — TODO

Web version first. CLI (`bible`) after web is done.

See [SESSION.md](./SESSION.md) for current state and
[decisions/](./decisions/README.md) for the *why* behind each design
choice below.

---

## Design decisions (locked)

- **Storage philosophy:** original book file = source of truth for text.
  DB stores only metadata + embeddings + chunk ranges. No full text persisted.
- **Chunking:** configurable via `CHUNK_PAGES` env var (default `1`).
  Each chunk = N consecutive pages, one embedding per chunk.
- **Re-embed:** per-book + "redo all" admin button. Required when changing
  `CHUNK_PAGES` or model.
- **Search modes (combinable):**
  1. tag filter (pure, no semantic)
  2. title/filename lexical
  3. semantic content (vector KNN over chunks)
- **Search response:** flat ranked hits; optional `?group_by_book=true`.
  Frontend groups for display, bible CLI uses flat.
- **Snippets:** generated on-demand per hit (open file, extract chunk text,
  slice around query). Not stored.
- **Sub-page pinpoint** inside chunk: v2.
- **Tags:** flat, no `kind` field, no `created_at`. Domain exposes
  `book.tags: list[Tag]`; storage uses junction table.
- **Auto-suggest tags:** v2.
- **Highlights:** v2.
- **Ingest:** background task; book status `pending → ready | failed`.
- **Folder scan:** drop files into `LABOOKE_IMPORT_DIR` and trigger
  `POST /api/admin/scan`; scanner reuses `IngestService`. Files move
  to `data/books/{sha256}.{ext}` on success. See
  [decision 0014](./decisions/0014-folder-scan-ingest.md).
- **Dedup:** sha256 on upload; merge tags into existing book.
- **Model storage:** mounted volume `models:/root/.cache/huggingface`.
- **Dev proxy:** Vite forwards `/api/*` to FastAPI (no CORS).
- **Migrations:** hand-rolled numbered SQL files, version tracked in DB.

---

## Phase 0 — Bootstrap
- [x] git init, .gitignore, TODO.md
- [x] README with quickstart
- [x] uv workspace `pyproject.toml` at root (Python pinned 3.12)
- [x] `packages/core/` skeleton (pyproject, src layout, domain models, config, empty submodule stubs)
- [x] `packages/api/` skeleton (FastAPI app, `/healthz`, `/api/config`, env-driven `run()`)
- [x] `frontend/` Vite + React + TS scaffold (proxy via `VITE_API_URL`)
- [x] `docker-compose.yml` + `docker/api.Dockerfile` + `docker/frontend.Dockerfile` + nginx conf
- [x] `.env.example` (root + frontend)
- [x] ruff + ruff-format config
- [x] prettier config (eslint shipped by Vite scaffold)
- [x] pytest config (importlib mode, both packages on path)
- [x] vitest + RTL config in `frontend/`
- [x] `scripts/test.sh` (backend + frontend)
- [ ] Test fixtures dir: `tests/fixtures/` with small sample PDF, EPUB, TXT (deferred to Phase 1 ingest tests)

## Phase 1 — Core lib (`packages/core`)

### Domain models (Pydantic v2)
- [x] `Book` (id, sha256, path, title, author, format, page_count, status, ingest_error, tags: list[Tag])
- [x] `BookStatus` enum (`pending | ready | reembedding | failed`)
- [x] `Tag` (id, name, slug, color)
- [x] `Chunk` (id, book_id, page_start, page_end)
- [x] `SearchHit` (book_id, page_start, page_end, snippet, score)
- [x] `Bookmark` (id, book_id, page_no, label, note)
- [x] `ReadingProgress` (book_id, page_no, updated_at)
- [x] `PageText` (page_no, text) — transient, never persisted

### Extractors (`extract/`)
- [x] `Extractor` protocol: `pages(path) -> Iterator[PageText]`, `page_text(path, n) -> str`, `page_count(path) -> int`
- [x] `PdfExtractor` (PyMuPDF)
- [x] `EpubExtractor` (ebooklib) — yields per-chapter/section as "page"
- [x] `TextExtractor` (txt/md, fixed N-line "pages" or paragraph-grouped)
- [x] Cover thumbnail extraction (PDF page 1 → webp, EPUB cover, MD/TXT placeholder)
- [x] Factory `for_format(fmt) -> Extractor`

### Embeddings (`embed/`)
- [x] Lazy singleton loader for `BAAI/bge-small-en-v1.5`
- [x] `encode(texts: list[str]) -> ndarray`
- [x] Idle-unload hook (optional, to keep RAM low)
- [x] Chunker: groups pages by `CHUNK_PAGES` env var

### Storage (`store/`)
- [ ] `schema.sql` (books, tags, book_tags, chunks, vec_chunks, bookmarks, reading_progress, schema_version)
- [x] `db.py` connect + load sqlite-vec + run migrations
- [x] Hand-rolled migrator: `migrations/0001_init.sql`, ordered, version-tracked
- [x] `BooksRepo` (insert, list, get, get_by_sha256, set_status, delete, filter by tags + lexical title/filename)
- [x] `TagsRepo` (CRUD, merge, counts)
- [x] `ChunksRepo` (insert, list_for_book, delete_for_book)
- [x] `VectorsRepo` (insert, knn with optional book_id filter)
- [x] `BookmarksRepo`, `ProgressRepo`
- [x] Seed-tag inserter (idempotent on first run)

### Services (`services/`)
- [x] `IngestService.ingest_book(path, tags) -> Book`
  - sha256 dedup → return existing if found, merge tags
  - insert pending row, return book_id
  - schedule background ingest (extract → chunk → embed → store → status=ready)
- [x] `LibraryScanner.scan() -> ScanResult` — walks
  `LABOOKE_IMPORT_DIR`, calls `IngestService` per supported file,
  moves on success, leaves failures in place
- [x] `ReembedService.reembed_book(id)`, `.reembed_all()`
- [x] `SearchService.search(q, tags, tag_mode, exclude, k, mode='semantic|lexical') -> list[SearchHit]`
  - tag filter applied first to narrow book_id set
  - then either vector KNN (semantic) or LIKE on title/filename (lexical)
- [x] `SnippetService.snippet_for_hit(hit, query) -> str` — opens file, extracts chunk, slices around query
- [x] `ReaderService.get_page(book_id, page_no) -> PageText` — direct file read, no DB hit
- [x] `LibraryService` (list/filter books with tag + lexical filters)

### Tests (core)
- [x] One test per extractor with a fixture file (PDF, EPUB, TXT, MD)
- [x] Cover extraction smoke test per format
- [x] Embed model: mock in unit tests, real model in one integration test
- [x] Repo tests: in-memory SQLite, fresh DB per test
- [x] Migrator: applies in order, idempotent, tracks version correctly
- [x] `IngestService` round-trip: ingest → search hits expected page range
- [x] `IngestService` sha256 dedup: same file twice → one book, tags merged
- [x] `SearchService` tag filter: AND, OR, exclude correctness
- [x] `SearchService` semantic + tag filter combined
- [x] `SearchService` lexical mode: title and filename LIKE
- [x] `SnippetService` returns substring containing query keywords
- [x] `ReaderService.get_page` returns correct text without DB text storage
- [x] `ReembedService` deletes old chunks/vectors before regenerating
- [x] `TagsRepo` merge: vectors and book_tags repoint correctly
- [x] Seed-tag inserter idempotent
- [x] `CHUNK_PAGES` change: reembed produces new chunk count
- [x] Coverage target: ≥80% on `services/` and `store/`
  (measured 2026-05-25: services 95%, store 100%, combined 97%)

## Phase 2 — API (`packages/api`)
- [x] FastAPI app, lifespan inits services + runs migrations
- [x] `deps.py` providers
- [x] Request/response schemas (separate from domain)
- [x] Exception handler → JSON `{code, message}`
- [x] structlog JSON logging + request-id middleware
- [x] CORS only for dev origin (prod = same-origin via nginx)
- [x] Routes:
  - [x] `POST   /api/books` (multipart upload + optional tag ids) → 202 `{book_id, status}`
  - [x] `GET    /api/books?tags=&tag_mode=&exclude=&q=&search=lexical`
  - [x] `GET    /api/books/{id}` (poll for status during ingest)
  - [x] `DELETE /api/books/{id}` (removes file + chunks + vectors)
  - [x] `GET    /api/books/{id}/file` (stream raw, for pdf.js / epub.js)
  - [x] `GET    /api/books/{id}/cover` (webp thumb)
  - [x] `GET    /api/books/{id}/pages/{n}` (returns `PageText`, on-demand extract)
  - [x] `POST   /api/books/{id}/reembed` (background)
  - [x] `POST   /api/admin/reembed-all` (background)
  - [x] `POST   /api/admin/scan` (background; returns `ScanResult` once done or 202 + status)
  - [x] `POST   /api/books/{id}/tags` / `DELETE .../tags/{tag_id}`
  - [x] `GET    /api/tags`
  - [x] `POST   /api/tags`
  - [x] `PATCH  /api/tags/{id}` (rename / recolor)
  - [x] `DELETE /api/tags/{id}`
  - [x] `POST   /api/tags/merge`
  - [x] `GET    /api/search?q=&tags=&tag_mode=&k=&group_by_book=false`
  - [x] `GET/POST /api/books/{id}/bookmarks`, `DELETE /api/bookmarks/{id}`
  - [x] `GET/PUT /api/books/{id}/progress`
- [x] Background task runner (FastAPI `BackgroundTasks` v1; revisit if heavy)
- [x] OpenAPI verified at `/docs`

### Tests (api)
- [x] `TestClient` fixture with overridden deps (in-memory DB, fake embedder, fake extractor)
- [x] One happy-path test per route (status + body shape)
- [x] Upload returns 202 + pending status; polling flips to ready
- [x] Upload duplicate (same sha256) returns existing book + merged tags
- [x] Lexical book search by title and filename
- [ ] Semantic search with tag filter combined (covered at core layer; API-level deferred — needs real embedder)
- [x] `group_by_book=true` returns grouped shape
- [x] Reembed deletes old vectors and inserts new (core layer)
- [x] Error mapping: domain errors → correct HTTP status + JSON shape
- [x] Bookmark + progress round-trip

## Phase 3 — Frontend (`frontend/`)

### Setup
- [ ] React Router v6 routes: `/`, `/read/:id`, `/tags`
- [ ] CSS Modules (no Tailwind)
- [ ] TanStack Query
- [ ] `npm run gen-types` from `/openapi.json` via `openapi-typescript`
- [ ] `api/client.ts` typed fetch wrapper
- [ ] Dark mode toggle (CSS variables)
- [ ] Vite proxy: `/api` → `http://localhost:8000`

### Library page (`features/library`)
- [ ] Tag sidebar with counts, click-to-filter, shift-click multi, ALL/ANY toggle, exclude (alt-click)
- [ ] Book grid: cover thumb, title, author, tag chips, progress bar, status badge (pending/failed)
- [ ] Search bar with mode pill: `[Title] / [Semantic]`, combined with tag filter
- [ ] Search results: grouped by book (uses `?group_by_book=true`), each card shows top page snippets, click → reader at page
- [ ] Upload dropzone (drag-drop multi-file) → modal with title/author edit + tag picker
- [ ] Upload returns immediately, book card appears with "ingesting..." spinner
- [ ] Polling hook for pending books → refetch on status change
- [ ] Per-book actions: rename, edit tags, redo embeddings, delete

### Reader page (`features/reader`)
- [ ] Route picks viewer by format
- [ ] `PdfViewer` (pdfjs-dist) — pulls `/api/books/{id}/file`
- [ ] `EpubViewer` (epubjs)
- [ ] `TextViewer` (md/txt)
- [ ] Page change → debounced `PUT /progress`
- [ ] Bookmark button → add/remove on current page
- [ ] Bookmark drawer (list, jump, edit note, delete)
- [ ] Tag chips clickable → back to library filtered by that tag

### Tags page (`features/tags`)
- [ ] List all tags with counts, recolor, rename, delete (with confirm)
- [ ] Create new tag
- [ ] Merge tags (pick source + target)

### Admin
- [ ] "Redo all embeddings" button (settings/admin section)
- [ ] "Scan import folder" button (shows count ingested / skipped / failed)
- [ ] Show current `CHUNK_PAGES`, model name, import dir path, total chunks/vectors stats

### Tests (frontend)
- [ ] vitest + RTL setup, jsdom env
- [ ] `api/client.ts` unit tests with `msw`
- [ ] Hook tests: `useBooks`, `useSearch`, `useUpload`, `useBookStatus` (polling)
- [ ] Component tests:
  - [ ] `BookGrid` renders books, shows pending state, click navigates
  - [ ] `UploadDropzone` accepts files, calls api, shows progress
  - [ ] Tag sidebar filter mode toggle, exclude
  - [ ] `SearchBar` debounces, switches semantic/lexical mode
  - [ ] `Reader` route picks correct viewer per format (mock pdf.js / epub.js)
  - [ ] Redo embeddings button calls api + reflects status
- [ ] Snapshot tests for stable presentational components

## Phase 4 — Docker + polish
- [x] `docker/api.Dockerfile` (python:3.12-slim, uv, sqlite-vec preinstalled)
- [x] `docker/frontend.Dockerfile` (multi-stage: node build → nginx static)
- [x] `docker-compose.yml`:
  - [x] api service
  - [x] frontend service (nginx serves SPA + proxies `/api` to api)
  - [x] volumes: `data:/data` (books + db), `models:/root/.cache/huggingface`
- [x] Healthchecks (api `/healthz`, frontend nginx)
- [x] README: install + run + add-book + search demo + env reference
- [x] Measure standby RAM (target <250MB total; measured 173.0 MiB on 2026-05-27)

## Phase 5 — Bible CLI (`packages/bible`) — AFTER WEB IS DONE
- [x] Typer entrypoint, depends on `core`
- [x] `bible search <query> [--tag x --tag y --any] [-k 10]` → hit list, numbered
- [x] `bible books [--tag linux]` → list books only (no semantic)
- [x] `bible tags` → list tags + counts
- [x] `bible tag <book_id> +linux -fiction` → edit tags
- [x] `bible books` → list library
- [x] `bible scan` → run the same import-folder scan from the terminal
- [x] TUI pager (prompt_toolkit):
  - [x] Render page text, wrap to terminal width (lazy fetch via `ReaderService.get_page`)
  - [x] Status bar: `book — page N/M`
  - [x] Keys: `j/k` line scroll, `n/p` next/prev page, `g/G` first/last, `/` in-book search, `q` quit
- [x] History of past queries (`bible history`)
- [x] Open last (`bible last`)

### Tests (bible)
- [x] Typer `CliRunner` per command
- [x] TUI key handler unit tests (j/k/n/p/g/G/q/ /)
- [x] Lazy page fetch: only requested pages loaded (mock `ReaderService`)
- [x] Tag filter flag parsing (`--tag x --tag y --any`)

## Cleanup técnico pendente (knip + análise de bundle)

### Dead code / exports desnecessários
- [ ] `src/api/reader.ts` — remover `export` de `getPageText` e `PageTextOut` (não usados fora do arquivo)
- [ ] `src/features/library/hooks/useBooks.ts` — remover `export` de `booksQueryKey` (interna)
- [ ] `src/features/library/hooks/useSearch.ts` — remover `export` de `searchQueryKey` e `SearchGroupOut`, `SearchHitOut` (internos)
- [ ] `src/api/books.ts` — remover `export` de `BookCreateResponse` (só usada em `upload.ts`)

### Dev dependencies
- [ ] Remover `prettier` do `package.json` (instalada mas sem config e sem uso no CI)
- [ ] Avaliar manter ou remover `openapi-typescript` (rodou 1x para gerar `openapi.d.ts`; pode ficar como ferramenta manual documentada)

### Bundle
- [ ] Investigar se `epubjs` pode ser substituída por algo menor — puxa `jszip` (201KB), `localforage` (64KB) e `sax` (16KB) que juntos somam ~280KB raw sem benefício aparente para o uso atual (leitura linear paginada)

---

## Deferred / v2
- [ ] Filesystem watcher for auto-scan (replaces manual trigger)
- [ ] Auto-suggest tags on ingest (embed tag names/descriptions, cosine vs chunks)
- [ ] Sub-page pinpoint inside large CHUNK_PAGES chunks
- [ ] Highlights (PDF rects + EPUB CFI, color, note)
- [ ] Hierarchical tags (`tech/linux`)
- [ ] Folder watch for auto-ingest
- [ ] Calibre library import
- [ ] Multi-user accounts
- [ ] Topic view (group hits across books w/ summary)
- [ ] Notes export
- [ ] WebSocket ingest status (replace polling)
