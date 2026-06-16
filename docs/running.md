# Rodando o labooke

→ [overview.md](overview.md) | [docker.md](docker.md)

## Docker (recomendado)

```bash
# 1. variáveis de ambiente
cp .env.example .env

# 2. build + start (primeira vez baixa o modelo ~130 MB)
docker compose up --build -d

# 3. acessar
open http://localhost:8080   # ou a porta em FRONTEND_PORT
```

Rebuild do frontend (após mudanças de código):
```bash
docker compose build --no-cache frontend && docker compose up -d
```

## Dev local

```bash
# backend
cp .env.example .env
uv sync
uv run labooke-api          # API em LABOOKE_API_HOST:LABOOKE_API_PORT

# frontend (outro terminal)
cd frontend
npm install
npm run dev                 # proxy /api/* → backend
```

Docs interativas: `http://localhost:8000/docs`

## CLI bible

Requer o servidor rodando. A API é exposta em `localhost:8010` pelo Docker.

```bash
uv run bible books
uv run bible search "design patterns"
uv run bible read 15 -p 42
```

→ Ver [bible.md](bible.md) para todos os comandos.

## Testes de arquitetura (retrieval)

Compara diferentes estratégias de busca (semântico, híbrido, cross-encoder):

```bash
# da raiz do repositório, com o servidor rodando
PYTHONPATH=. uv run python testes_arquitetura/run.py "sua query" --retriever all
PYTHONPATH=. uv run python testes_arquitetura/run.py "design patterns" --k 5
```

→ Ver [testes_arquitetura/README.md](../testes_arquitetura/README.md) para detalhes.

## Testes automatizados

```bash
uv run pytest -q                   # backend
cd frontend && npx vitest run      # frontend
./scripts/test.sh                  # ambos
```

Para acesso de outro dispositivo, libere `FRONTEND_PORT` no firewall  
ou use túnel (Tailscale / ngrok). → Ver [docker.md](docker.md) para env vars.
