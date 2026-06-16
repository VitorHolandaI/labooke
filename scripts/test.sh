#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "--- backend ---"
uv run pytest -q

echo "--- frontend ---"
npm --prefix frontend test
