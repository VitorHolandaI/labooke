# Continue — hand-off note

Short, mutable note for whoever picks up next. Pair with the
permanent docs: [SESSION.md](./SESSION.md) (project resume),
[TODO.md](./TODO.md) (work plan), [DESIGN.md](./DESIGN.md), and
[decisions/README.md](./decisions/README.md).

## Where we are

**Branch:** `feat/core-services` (stacked on `feat/core-embed`). Run
`git log --oneline feat/core-embed..feat/core-services` to see just the
service-layer slice.

**Just finished:**

- Phase 1 service work on `feat/core-services`:
  1. `LibraryService` now hydrates `Book.tags` for detail/list views
  2. `ReaderService.get_page()` reads logical pages directly from source files
  3. `SnippetService.snippet_for_hit()` extracts on-demand query snippets
  4. `SearchService.search()` now supports lexical + semantic modes with tag filtering
  5. `BookEmbeddingPipeline` rebuilds chunks/vectors from source files
  6. `IngestService` now handles sha256 dedup, managed copies, tagging, and ingest status
  7. `ReembedService` now rebuilds one book or all books through the same pipeline
  8. `LibraryScanner.scan()` now ingests supported files from `LABOOKE_IMPORT_DIR`
- Supporting storage/config updates:
  1. `Settings.import_dir` now defaults to `data/inbox`
  2. `BooksRepo.set_status()` now optionally updates `page_count`
  3. `AGENTS.md` now requires docstrings on public functions and public methods

**Validation:**

- `uv run pytest -q packages/core/tests` → `149 passed`
- `uv run python tools/pyquality.py packages/core/src/labooke_core/services -v`
  → quality gate passed, grade `A (97.9/100)`

## What's next (in order)

1. **Push + merge stacked branches** — land `feat/core-extract`,
   `feat/core-embed`, and `feat/core-services` in order.
2. **API layer** — wire FastAPI lifespan/deps/schemas/routes on top of
   the now-complete core services.
3. **Core lib follow-ups** — add real fixture files and measure/report
   explicit `services/` + `store/` coverage against the ≥80% target.

## How to resume

```bash
cd /home/vitor/git/labooke
git switch feat/core-services
uv sync
uv run pytest -q packages/core/tests
uv run python tools/pyquality.py packages/core/src/labooke_core/services
# then pick up from "What's next" above
```

## Reminders (from AGENTS.md / memory)

- Small commits, `type(scope): subject` format, one concern each
- Feature branches; no commits direct to `main`
- Cross-link any new markdown to related docs
- `trash`, never `rm`
- Hosts/ports from env vars only
- Run `uv run python tools/pyquality.py packages` before merging a
  big chunk
