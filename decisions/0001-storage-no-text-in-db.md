# 0001 — Original file is source of truth; page text stored only for BM25

**Status:** amended (migration 0003)

## Context

Books (PDF, EPUB, TXT/MD) need to be searchable semantically and readable
page-by-page. Two storage strategies were considered:

1. Extract every page during ingest, store text + embedding in SQLite.
   Fast page fetch, but ~5-15MB per 300-page book; 100 books ≈ 1GB.
2. Extract on ingest only to embed; persist only embeddings + chunk page
   ranges; re-extract from the original file on demand for reads.

## Decision

Option 2 with a targeted amendment. The DB stores:

```
chunks(id, book_id, page_start, page_end, text)  -- text kept for BM25
vec_chunks(chunk_id, embedding)                   -- sqlite-vec
chunks_fts(text)                                  -- FTS5 BM25 index
```

The `text` column in `chunks` holds the extracted page text for each
chunk so that BM25 full-text search can run without re-opening the
original file. The on-disk file at `books.path` remains the source of
truth for reading (the reader still re-extracts from the file).

Storing text per chunk (not per page) keeps the footprint bounded:
`CHUNK_PAGES=1` ≈ 500 words/chunk; 300 chunks × ~2KB = ~600KB per book.
100 books ≈ 60MB — acceptable and well within SQLite's sweet spot.

## Consequences

- DB is larger than the original design (~60MB/100 books instead of ~5MB),
  but still orders of magnitude smaller than storing full page text.
- BM25 search (hybrid mode) runs entirely in SQLite without file I/O.
- Reembed reinserts chunk text; no separate backfill needed.
- Search snippets for the reader are still generated on-demand from the
  file (`SnippetService`) to avoid duplicating that code path.
- Books become unusable if the original file is deleted. Mitigated by
  storing files inside the project's `data/` volume.

## Related

- [0003 — Search modes](0003-search-modes.md) — snippets are extracted
  from the file on demand because text isn't stored.
- [0004 — `CHUNK_PAGES` env var](0004-chunk-pages-env-var.md) — chunk
  granularity sits on top of this storage shape.
- [0005 — Background ingest](0005-background-ingest.md) — the ingest
  pipeline only embeds; it never persists page text.
- [0013 — CLI deferred](0013-cli-deferred-after-web.md) — the bible CLI
  reads pages directly from the same files.
