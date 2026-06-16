# 0014 — Folder-scan ingest as a second upload path

**Status:** accepted

## Context

The HTTP upload path
([decision 0005](0005-background-ingest.md)) is fine for one-off drops
from the browser, but the user often has a pile of books already on
disk and doesn't want to drag-and-drop each one. They want to drop
files into a folder and have the library pick them up.

## Decision

Add a **scan** path that reuses the existing `IngestService`.

- New env var `LABOOKE_IMPORT_DIR` (default `./data/inbox`). Anything
  placed there is a candidate.
- `LibraryScanner.scan()` walks the import dir, filters supported
  extensions (`.pdf`, `.epub`, `.txt`, `.md`), and calls
  `IngestService.ingest_book(path, tags=[])` for each.
- Existing sha256 dedup
  ([decision 0006](0006-sha256-dedup.md)) ensures a re-run is a no-op
  for already-known files.
- After successful ingest the source file is **moved** into the managed
  location `data/books/{sha256}.{ext}`. Inbox stays empty between
  scans. (Move, not copy, so the inbox is a clean queue.)
- Files that fail to ingest stay in the inbox; the failed book row
  carries `status='failed'` with the error.
- Tags are not assigned by the scanner — the user adds them later from
  the library UI. (Auto-suggest may help once it ships;
  see [decision 0011](0011-defer-auto-suggest-and-highlights.md).)

### Triggers

- **v1:** on-demand only.
  - `POST /api/admin/scan` from the web admin page (button).
  - `bible scan` subcommand on the CLI (post-web phase).
- **v2:** filesystem watcher (e.g. `watchdog`) auto-triggers on new
  files. Deferred to keep v1 RAM low and avoid platform-specific
  weirdness.

## Consequences

- Bulk-loading a library is "copy files into `inbox/`, hit Scan".
- The scanner reuses every guarantee of single-file upload: dedup,
  background ingest, status, error reporting.
- The inbox doubles as a visible "failed" queue: anything still in
  there after a scan needs attention.
- v1 mismatch: scanned books arrive untagged. The user accepts this —
  tagging is a manual step they want control over.
- Adds two files: `LibraryScanner` (service) and a thin admin route /
  CLI subcommand.

## Related

- [0005 — Background ingest](0005-background-ingest.md) — scan reuses
  the same service and background machinery.
- [0006 — sha256 dedup](0006-sha256-dedup.md) — makes scans idempotent.
- [0007 — Env vars](0007-no-hardcoded-endpoints.md) — `LABOOKE_IMPORT_DIR`
  is just another `LABOOKE_*` setting.
- [0011 — Auto-suggest deferred](0011-defer-auto-suggest-and-highlights.md)
  — would automate tag assignment for scanned books eventually.
