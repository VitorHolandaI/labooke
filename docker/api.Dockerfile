# syntax=docker/dockerfile:1

# ── builder: tem build-essential para compilar extensões C ──────────────────
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /usr/local/bin/uv

# manifests separados do source para reaproveitar o layer de deps no cache
COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml  packages/core/pyproject.toml
COPY packages/api/pyproject.toml   packages/api/pyproject.toml
COPY packages/bible/pyproject.toml packages/bible/pyproject.toml

# stubs vazios para uv resolver o workspace antes do source real chegar
RUN mkdir -p packages/core/src/labooke_core \
             packages/api/src/labooke_api \
             packages/bible/src/labooke_bible \
    && touch packages/core/src/labooke_core/__init__.py \
             packages/api/src/labooke_api/__init__.py \
             packages/bible/src/labooke_bible/__init__.py

RUN uv sync --frozen --no-dev

COPY packages/ packages/

# ── runtime: imagem final sem ferramentas de build ──────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LABOOKE_DATA_DIR=/data \
    LABOOKE_IMPORT_DIR=/data/inbox

WORKDIR /app

# apenas libs de runtime do PyMuPDF — sem build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv   /app/.venv
COPY --from=builder /app/packages /app/packages

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "labooke_api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
