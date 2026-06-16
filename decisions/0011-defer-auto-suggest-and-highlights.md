# 0011 — Auto-suggest tags and PDF/EPUB highlights deferred to v2

**Status:** accepted

## Context

Both features were initially in scope for v1.

- **Auto-suggest tags** — embed tag names/descriptions and cosine-match
  against book chunks during ingest to pre-check likely tags.
- **Highlights** — persist user-selected text ranges (PDF rects, EPUB
  CFI) with color and optional note; render as overlays in the reader.

## Decision

Both ship in v2.

## Reasons

- Auto-suggest quality depends heavily on tag name expressiveness; would
  need an optional `description` field per tag to embed. Better to wait
  until there's a real library and see which tags actually get used.
- Highlights require both backend persistence (text + rects + CFI) and
  reader-side overlay rendering, plus an edit/delete UI. Significant
  scope for a non-essential feature.

## Consequences

- v1 keeps tag UI fully manual but fast: tag picker on upload, click-to-
  edit on book cards, tag manager page.
- v1 readers offer page-level bookmarks only (page + optional label and
  note), no in-page highlights.
- The schema for highlights is not pre-baked; it lands when the feature
  does.

## Related

- [0002 — Tags flat](0002-tags-flat-with-junction-table.md) — the tag
  model would gain an optional `description` field if/when auto-suggest
  ships.
- [0001 — No text in DB](0001-storage-no-text-in-db.md) — auto-suggest
  would reuse the existing chunk embeddings rather than re-extract.
