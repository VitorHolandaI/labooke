# labooke — visão geral

Biblioteca pessoal de livros auto-hospedada. PDF, EPUB, TXT, MD.
Organização por tags, busca semântica, leitor integrado, standby < 175 MB.

![Library](images/library-amber.png)

## Stack

| Camada     | Tecnologia                                              |
|------------|---------------------------------------------------------|
| Backend    | Python 3.12, FastAPI, Pydantic v2, SQLite + sqlite-vec  |
| Embeddings | sentence-transformers (`BAAI/bge-small-en-v1.5`)        |
| Frontend   | React + Vite + TypeScript, CSS Modules, TanStack Query  |
| Viewers    | pdf.js (PDF), epub.js (EPUB), renderer próprio (TXT/MD) |
| Deploy     | docker compose — 2 containers no mesmo host             |

## Fluxo principal

```
Upload / pasta inbox
       ↓
  IngestService  →  extrai texto  →  chunks  →  embeddings  →  sqlite-vec
       ↓
  Biblioteca  →  busca  →  leitor  →  bookmarks / progresso
```

## Documentação

| Arquivo                        | Conteúdo                              |
|--------------------------------|---------------------------------------|
| [running.md](running.md)       | Como rodar (Docker e dev local)       |
| [upload.md](upload.md)         | Upload de livros e pipeline de ingest |
| [reader.md](reader.md)         | Leitor: modos, tela cheia, bookmarks  |
| [search.md](search.md)         | Busca por título, semântica e tags    |
| [api.md](api.md)               | Endpoints HTTP                        |
| [frontend.md](frontend.md)     | Estrutura do frontend                 |
| [docker.md](docker.md)         | Docker, env vars, RAM                 |
| [migracao.md](migracao.md)     | Migração, backup e recuperação        |

Decisões de arquitetura: [../decisions/](../decisions/README.md)
