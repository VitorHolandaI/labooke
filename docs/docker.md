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

| Volume   | Montado em     | Conteúdo                      |
|----------|----------------|--------------------------------|
| `data`   | `/data` (api)  | SQLite, livros, covers, inbox  |

## Env vars principais

| Variável                        | Padrão            | Descrição                              |
|---------------------------------|-------------------|----------------------------------------|
| `LABOOKE_DATA_DIR`              | `./data`          | Raiz dos dados                         |
| `LABOOKE_IMPORT_DIR`            | `./data/inbox`    | Pasta de scan                          |
| `LABOOKE_EMBED_BASE_URL`        | *(vazio)*         | URL raiz do Ollama para embeddings     |
| `LABOOKE_EMBED_MODEL`           | `bge-m3`          | Modelo multilíngue no Ollama           |
| `LABOOKE_EMBED_TIMEOUT_SECONDS` | `120`             | Timeout de embedding                   |
| `LABOOKE_CHUNK_PAGES`           | `1`               | Páginas por chunk de embedding         |
| `FRONTEND_PORT`                 | `8080`            | Porta exposta no host (frontend)       |
| `API_PORT`                      | `8010`            | Porta exposta no host (API)            |

## Modelo de embeddings

O BGE-M3 roda no Ollama externo; o container da API não carrega PyTorch nem
pesos locais, então não há volume de modelos nem worker separado. O endpoint
pode ser sobrescrito no Admin e volta ao valor do `.env` quando o override é
removido. Ver [search.md](search.md).
