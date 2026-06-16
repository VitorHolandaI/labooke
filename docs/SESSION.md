# Session Resume — 2026-05-30

Captures where the project stands after the Phase 3 + quality + polish
session. Pair with [TODO.md](./TODO.md) (work plan) and
[decisions/](./decisions/) (locked architecture decisions).

---

## What labooke is

A local, low-RAM web book library and reader for PDF, EPUB, and TXT/MD.
Tag-first organization, semantic search by content, lexical search by
title/filename. A companion CLI named `bible` (shipped after web) opens
the same library from the terminal and pages through results lazily.

Built explicitly as a lighter alternative to Booklore (target standby
RAM < 250MB total vs Booklore's ~700MB; measured 173.0 MiB on 2026-05-27).

## What's complete

**Everything from the previous session** (backend core + API + frontend
skeleton + Docker + bible CLI) — see git history for details.

**Frontend — Phase 3 (complete)**

Library page, reader, tags page, and admin section are fully wired to
the API. Key features:
- Library: tag sidebar (click include, alt-click exclude, ALL/ANY toggle),
  book grid with cover thumbs + status badges + progress bar, lexical and
  semantic search (with snippet results grouped by book), multi-file upload
  dropzone with animated progress, per-book actions (rename, edit tags,
  re-embed, delete with confirm), polling hook for pending-status books
- Reader: PDF (pdfjs-dist, single/double page, lazy load), EPUB (epubjs,
  paginated, location-based progress), TXT/MD (chunked, minimal Markdown
  renderer), swipe gestures, fullscreen mode, bookmarks drawer, debounced
  progress sync, tag chips link back to filtered library
- Tags page: list with counts, recolor, rename, delete with confirm, create
  new, merge two tags
- Admin page: re-embed all, scan import folder, current config stats
- Dark/light mode toggle

**Docker image size reduction (2026-05-30)**

- `pyproject.toml`: added `torch>=2.0,<2.7` as a direct root dependency
  with `[tool.uv.sources] torch = [{ index = "pytorch-cpu" }]` so uv
  resolves `torch 2.6.0+cpu` from the PyTorch CPU CDN instead of the
  default `torch 2.12.0` GPU wheel from PyPI
- This removed 18 nvidia/CUDA packages (~3–4 GB) from the image
- `docker/api.Dockerfile`: already multi-stage (builder with
  build-essential → runtime with only libgl1 + libglib2.0-0); no extra
  swap step needed — `uv sync --frozen --no-dev` now installs CPU torch
  directly from the lockfile

**pnpm migration (2026-05-30)**

- Frontend switched from npm to pnpm
- `pnpm-lock.yaml` generated, `package-lock.json` deleted
- `docker/frontend.Dockerfile` updated to use `corepack enable pnpm` +
  `pnpm install --frozen-lockfile --ignore-scripts`
- `frontend/pnpm-workspace.yaml` added with `onlyBuiltDependencies: [msw]`
  (pnpm 11 no longer reads the `pnpm` field from `package.json`)
- `tsconfig.app.json` now excludes `src/test` and `*.test.*` so `tsc -b`
  does not type-check the test setup file that imports `undici`

**Frontend bugs fixed (2026-05-30)**

- `upload.ts`: rewritten from XHR to `fetch` — works correctly with msw in
  tests; removed `onProgress` (progress bar animated fallback already
  handles missing byte events)
- `TextViewer`: swipe `goNext` now clamps to `totalPages` (previously
  could exceed last page); fixed forward-reference lint error by computing
  `pages`/`totalPages` before the callbacks and using `totalPagesRef`
- `EpubViewer`: after `locations.generate()` resolves, jumps to
  `initialPage` so bookmarks and stored progress land on the correct
  position; uses `initialPageRef` to avoid re-triggering the book-load
  effect when progress data loads late
- `PdfViewer`: captures `RenderTask` returned by `p.render()` and calls
  `.cancel()` on cleanup — rapid page navigation no longer stacks
  concurrent renders on the same canvas
- `useDebouncedProgress`: stale `initial` ref reset when `bookId` changes
  (React Router reuses component across navigation); `mutRef` updated in
  effect not during render (react-hooks/refs)

**Performance fix (2026-05-30)**

- `useTags()` moved from `BookCard` (called N times, N React Query
  subscribers) up to `LibraryPage` (one subscriber); `allTags: TagOut[]`
  passed as prop through `BookGrid → BookCard`. Tag invalidation now
  triggers a single re-render instead of N.

**Mobile responsiveness (2026-05-30)**

- Breakpoint: `≤640px`
- Library page: `flex-direction: column`; tag sidebar hidden by default,
  shown via a "☰ Filters" toggle button as a fixed slide-in overlay with
  backdrop tap-to-dismiss
- Reader page: title truncates with ellipsis; bookmark drawer becomes a
  fixed bottom sheet (65vh) when open, a floating "☆" FAB when closed
- App topbar: compact padding and font size on mobile
- Global `:focus-visible` outline added (2px accent, offset 2px) so
  keyboard focus is always visible

**Keyboard accessibility (2026-05-30)**

- `Modal`: focus trap on open (Tab/Shift-Tab cycle within panel, Escape
  closes, focus restored to triggering element on close)
- `BookActionsMenu`: on open focuses first menu item; ArrowDown/Up moves
  between items; Home/End jump to first/last; Escape closes and restores
  focus to the `⋯` trigger button; Tab closes the menu

**Code quality tooling added**

- `eslint-plugin-react-hooks` v7 wired and clean (0 errors)
- `knip` run: dead exports listed in TODO.md cleanup checklist
- `rollup-plugin-visualizer` added to `vite.config.ts` — generates
  `dist/stats.html` on every build for bundle inspection

## What's next

- **Cleanup checklist** (see TODO.md "Cleanup técnico pendente"):
  remove unused exports, drop `prettier` devDep, evaluate `epubjs` replacement
- **pyquality launcher** (see plan file): replace `tools/pyquality.py`
  copy with a thin launcher that fetches the canonical version from GitHub
- **v2 / deferred**: filesystem watcher, auto-suggest tags, highlights,
  hierarchical tags, WebSocket ingest status, Calibre import

## How to resume

```bash
cd /home/vitor/git/labooke

# verify backend
uv sync
./scripts/test.sh

# start dev (backend + frontend)
cp .env.example .env
cp frontend/.env.example frontend/.env
uv run labooke-api &
cd frontend && pnpm dev

# production build check
cd frontend && pnpm run build   # tsc -b + vite build, no test files
```

Read [decisions/README.md](decisions/README.md) before changing any
architectural piece — the why for each choice lives there.
