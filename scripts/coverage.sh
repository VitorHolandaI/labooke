#!/usr/bin/env bash
# Enforce the >=80% coverage gate on services/ and store/ called out in TODO.md.
set -euo pipefail

cd "$(dirname "$0")/.."

uv run pytest -q \
  --cov=labooke_core.services \
  --cov=labooke_core.store \
  --cov-report=term \
  --cov-fail-under=80 \
  packages/core/tests
