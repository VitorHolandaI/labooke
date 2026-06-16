# Docker

→ [overview.md](overview.md) | [running.md](running.md)

## Serviços

| Serviço    | Imagem base      | Porta interna | Descrição          |
|------------|------------------|---------------|--------------------|
| `api`      | python:3.12-slim | `8000`        | FastAPI + uvicorn  |
| `frontend` | nginx:1.27-alpine| `80`          | React build estático|

`frontend` depende de `api` (healthcheck). Nginx faz proxy de `/api/*`  
para o container `api` e serve SPA com fallback em `/`.

A porta `8010` é mapeada no host por padrão para evitar conflito com outros serviços.
Ajuste `API_PORT` se precisar expor a API em outra porta.

## Volumes

| Volume   | Montado em                    | Conteúdo                       |
|----------|-------------------------------|--------------------------------|
| `data`   | `/data` (api)                 | SQLite, livros, covers, inbox  |
| `models` | `/root/.cache/huggingface`    | Modelo de embeddings (~130 MB) |

## Env vars principais

| Variável                          | Padrão                   | Descrição                         |
|-----------------------------------|--------------------------|-----------------------------------|
| `LABOOKE_DATA_DIR`                | `./data`                 | Raiz dos dados                    |
| `LABOOKE_IMPORT_DIR`              | `./data/inbox`           | Pasta de scan                     |
| `LABOOKE_EMBED_MODEL`             | `BAAI/bge-small-en-v1.5` | Modelo HuggingFace                |
| `LABOOKE_EMBED_CACHE_MODEL`       | `false` (docker)         | `true` = modelo em processo (dev) |
| `LABOOKE_EMBED_WORKER_IDLE_SECONDS`| `60`                    | Worker desliga após N seg idle    |
| `LABOOKE_CHUNK_PAGES`             | `1`                      | Páginas por chunk de embedding    |
| `FRONTEND_PORT`                   | `8080`                   | Porta exposta no host (frontend)  |
| `API_PORT`                        | `8010`                   | Porta exposta no host (API)       |

## RAM (medido 2026-05-27)

| Estado                        | API      | Frontend | Total    |
|-------------------------------|----------|----------|----------|
| Standby, sem worker           | 151.8 MB | 10.9 MB  | 162.7 MB |
| Worker ativo (busca semântica)| 643.9 MB | 11.1 MB  | 655.0 MB |
| Após idle shutdown do worker  | 161.9 MB | 11.1 MB  | 173.0 MB |

`EMBED_CACHE_MODEL=false` isola o modelo em worker separado que desliga  
após ocioso — mantém standby baixo. Ver [search.md](search.md) para detalhes.
