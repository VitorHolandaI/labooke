# Architecture Decisions

Lightweight ADR-style records. One file per decision, numbered.

Format per file:
- **Status** — accepted / superseded / deprecated
- **Context** — what problem, what alternatives
- **Decision** — what we picked
- **Consequences** — what it costs and unlocks

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-storage-no-text-in-db.md) | Original file is source of truth; no full text in DB | accepted |
| [0002](0002-tags-flat-with-junction-table.md) | Flat tags; junction table hidden behind domain | accepted |
| [0003](0003-search-modes.md) | Three combinable search modes: tag, lexical, semantic | accepted |
| [0004](0004-chunk-pages-env-var.md) | Chunk size configurable via `CHUNK_PAGES` env var | accepted |
| [0005](0005-background-ingest.md) | Ingest runs in background; book status polled | accepted |
| [0006](0006-sha256-dedup.md) | Dedup uploads by sha256; merge tags on collision | accepted |
| [0007](0007-no-hardcoded-endpoints.md) | All hosts/ports/URLs come from env vars | accepted |
| [0008](0008-vite-proxy-no-cors.md) | Vite dev server proxies `/api`; no CORS in dev | accepted |
| [0009](0009-hand-rolled-migrations.md) | Numbered SQL migrations; no Alembic | accepted |
| [0010](0010-css-modules-no-tailwind.md) | CSS Modules over Tailwind for personal-scale UI | accepted |
| [0011](0011-defer-auto-suggest-and-highlights.md) | Auto-suggest tags and highlights deferred to v2 | accepted |
| [0012](0012-pyquality-as-gate.md) | Code quality verified via `tools/pyquality.py` | accepted |
| [0013](0013-cli-deferred-after-web.md) | Bible CLI ships only after web is complete | accepted |
| [0014](0014-folder-scan-ingest.md) | Folder-scan ingest as a second upload path | accepted |
