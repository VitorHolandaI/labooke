# 0006 — Dedup uploads by sha256; merge tags on collision

**Status:** accepted

## Context

Re-uploading the same PDF is easy to do by accident. Title-based dedup
is unreliable (renames, identical titles from different sources).

## Decision

On upload, compute sha256 of the file bytes before insert.

- Match → return the existing `Book`. Any tags supplied with the second
  upload are merged into the existing row.
- No match → insert as new, file stored at `data/books/{sha256}.{ext}`.

The sha256 is also the on-disk filename, eliminating name collisions.

## Consequences

- Idempotent uploads; safe to retry.
- The same file can sit in multiple "logical" collections (tags) without
  duplicating bytes or embeddings.
- Changes to file contents produce a different sha256 and therefore a
  different book; this is desirable for "I re-OCRed it" cases.

## Related

- [0005 — Background ingest](0005-background-ingest.md) — dedup is the
  first step of the upload handler before scheduling work.
