## Code style

- Functions: 4-20 lines. Split if longer.
- Files: under 500 lines. Split by responsibility.
- One thing per function, one responsibility per module (SRP).
- Names: specific and unique. Avoid `data`, `handler`, `Manager`.
  Prefer names that return <5 grep hits in the codebase.
- Types: explicit. No `any`, no `Dict`, no untyped functions.
- No code duplication. Extract shared logic into a function/module.
- Early returns over nested ifs. Max 2 levels of indentation.
- Exception messages must include the offending value and expected shape.

## Comments

- Keep your own comments. Don't strip them on refactor — they carry
  intent and provenance.
- Write WHY, not WHAT. Skip `// increment counter` above `i++`.
- Docstrings are required on public functions and public methods:
  intent, non-obvious args/returns when needed, and one usage example.
- Reference issue numbers / commit SHAs when a line exists because
  of a specific bug or upstream constraint.

## Tests

- Tests run with a single command: `<project-specific>`.
- Every new function gets a test. Bug fixes get a regression test.
- Mock external I/O (API, DB, filesystem) with named fake classes,
  not inline stubs.
- Tests must be F.I.R.S.T: fast, independent, repeatable,
  self-validating, timely.

## Dependencies

- Inject dependencies through constructor/parameter, not global/import.
- Wrap third-party libs behind a thin interface owned by this project.

## Structure

- Follow the framework's convention (Rails, Django, Next.js, etc.).
- Prefer small focused modules over god files.
- Predictable paths: controller/model/view, src/lib/test, etc.

## Formatting

- Use the language default formatter (`cargo fmt`, `gofmt`, `prettier`,
  `black`, `rubocop -A`). Don't discuss style beyond that.

## Logging

- Structured JSON when logging for debugging / observability.
- Plain text only for user-facing CLI output.

## Collaboration

- **Branch first.** New work goes on `feat/<name>`, `fix/<name>`, or
  `docs/<name>` branches. Don't commit directly to `main`. Open a PR
  on the Gitea remote for review.
- **Conventional Commits, small and focused.** Format:
  `type(scope): subject` (≤60 chars, imperative). One concern per
  commit; never bundle unrelated changes. Types: `feat`, `fix`,
  `docs`, `chore`, `refactor`, `test`, `ci`, `build`, `perf`.
- **Cross-link markdown docs.** ADRs, TODO, SESSION, README should
  link to related files (relative paths). See
  [decisions/README.md](./decisions/README.md).
- **Python quality gate:** `uv run python tools/pyquality.py packages`.
  See [decision 0012](./decisions/0012-pyquality-as-gate.md).
- **Deletes use `trash`, not `rm`.** Recoverable; protects against
  accidental data loss.
- **All hosts/ports/URLs from env vars.** Never hardcoded literals.
  See [decision 0007](./decisions/0007-no-hardcoded-endpoints.md).
- **CI on Gitea Actions** at `.gitea/workflows/`. Push to `main` and
  every PR trigger the test suite.

## memory

At the start of non-trivial tasks, call `memory_smart_search` with the
task keywords. Use `memory_save` or `memory_lesson_save` when capturing
decisions, patterns, or preferences worth keeping.
