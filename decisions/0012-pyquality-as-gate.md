# 0012 — Code quality verified via `tools/pyquality.py`

**Status:** accepted

## Context

The user maintains a local quality wrapper at
`~/git/python_quick_quality/pyquality.py` that orchestrates pylint,
flake8, bandit, radon, vulture, and mypy into a single graded report.

## Decision

A copy of `pyquality.py` lives at `tools/pyquality.py` in this repo
(alongside `tools/pyquality-requirements.txt`). Quality is checked by
running it directly:

```bash
uv run python tools/pyquality.py packages
```

It is **not** wired into `scripts/test.sh` or `uv` dependency groups; the
user runs it on demand.

Bandit's `B101` (assert used) is a false positive for pytest; the
`[tool.bandit]` block in `pyproject.toml` skips it and excludes the
`tests/` dirs. (Note: pyquality invokes bandit with explicit file paths
and without `-c`, so this config is currently not picked up — the test
asserts still appear in the report. The gate still passes at grade B.)

Docstrings on public functions are a project rule (per AGENTS.md);
pyquality disables `C0114/C0115/C0116` in pylint, so docstring
enforcement is by review, not by the tool.

## Consequences

- Quality is a discipline, not a CI blocker (yet).
- Adding pylint/flake8/bandit/radon/vulture/mypy to dev deps is left to
  the user (currently installed in the venv via `uv pip install`
  outside `pyproject.toml`).
- The copied tool drifts from upstream; refresh periodically by re-
  copying.
