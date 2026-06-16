# 0013 — Bible CLI ships only after the web app is complete

**Status:** accepted

## Context

The original brief had two deliverables: a web reader and a `bible` CLI
that searches the same library by embedding and pages through results
lazily in the terminal.

Building both in parallel would split focus and force every change to
satisfy two UIs.

## Decision

Web first. CLI starts only after the web app is shippable.

The CLI lives at `packages/bible/` and depends on `labooke-core`
directly — no HTTP. It opens the same SQLite file and reads pages from
the same on-disk files.

Render mode: text-only via PyMuPDF extraction (no image protocols). Nav:
pager-style (`j/k`, `n/p`, `g/G`, `/`, `q`) via prompt_toolkit.

## Consequences

- All API + frontend work happens against one coherent design.
- Once core is solid the CLI is mostly UI glue; small surface.
- Both UIs share the same library, embeddings, tags, bookmarks, and
  reading progress because they hit the same DB.

## Related

- [0001 — No text in DB](0001-storage-no-text-in-db.md) — the CLI reads
  pages directly from the original files, same as the web reader.
- [0003 — Search modes](0003-search-modes.md) — the CLI uses the flat
  search response shape.
- [0005 — Background ingest](0005-background-ingest.md) — the CLI never
  ingests; it relies on the web app or a CLI subcommand to do so via
  the same `IngestService`.
