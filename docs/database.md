# Estrutura do banco de dados

→ [overview.md](overview.md) | [models.md](models.md) | [migracao.md](migracao.md)

SQLite + [sqlite-vec](https://github.com/asg017/sqlite-vec). Um arquivo
único: `{LABOOKE_DATA_DIR}/labooke.db`. Migrations numeradas e
hand-rolled (sem Alembic) em
`packages/core/src/labooke_core/store/migrations/` — ver
[decisão 0009](../decisions/0009-hand-rolled-migrations.md).

## Tabelas

| Tabela            | Colunas principais                                      | Papel                          |
|-------------------|----------------------------------------------------------|--------------------------------|
| `books`           | `id`, `sha256`, `path`, `title`, `author`, `description`, `rag_text`, `format`, `page_count`, `status`, `ingest_error`, `created_at` | metadados do livro             |
| `tags`            | `id`, `name`, `slug` (único), `color`                    | tags planas                    |
| `book_tags`       | `book_id`, `tag_id` (PK composta)                        | junction livro↔tag             |
| `chunks`          | `id`, `book_id`, `page_start`, `page_end`, `text`        | range de páginas + texto (FTS) |
| `bookmarks`       | `id`, `book_id`, `page_no`, `label`, `note`              | marcações do leitor            |
| `reading_progress`| `book_id` (PK), `page_no`, `updated_at`                  | última página lida             |
| `settings`        | `key` (PK), `value`                                      | runtime config (Admin)         |
| `schema_version`  | `version`                                                | versão de migração aplicada    |

## Tabelas virtuais (sqlite-vec / FTS5)

| Tabela         | Tipo  | Conteúdo                                              |
|----------------|-------|--------------------------------------------------------|
| `vec_chunks`   | vec0  | `(chunk_id, embedding FLOAT[384])` — embeddings de chunks |
| `vec_summaries`| vec0  | `(book_id, embedding FLOAT[384])` — embedding do resumo |
| `books_fts`    | fts5  | índice de título (busca híbrida)                       |
| `chunks_fts`   | fts5  | índice BM25 do texto dos chunks                        |

Dimensão `384` = `intfloat/multilingual-e5-small`. Trocar de modelo
com dimensão diferente exige migration nova + re-embed total.

## Migrations

| #    | O que faz                                    |
|------|-----------------------------------------------|
| 0001 | schema inicial (books, tags, chunks, vec_chunks, bookmarks, progress) |
| 0002 | FTS5 sobre títulos                           |
| 0003 | `chunks.text` + FTS5 BM25 sobre chunks       |
| 0004 | `books.description` (resumo do LLM)          |
| 0005 | `vec_summaries` (embedding do resumo p/ RAG) |
| 0006 | tabela `settings` (runtime config do Admin)  |
| 0007 | `books.rag_text` (texto de busca p/ RAG)     |

Aplicadas por `migrator.migrate()` na ordem, com a versão registrada em
`schema_version`. Idempotente: rodar de novo não faz nada.

## Repositórios (`packages/core/src/labooke_core/store/`)

Cada tabela tem um repo dedicado que recebe a conexão pelo construtor:

- `books_repo.py` — `BooksRepo` (insert, get, find com filtros, update_*, delete, search_fts)
- `tags_repo.py` — `TagsRepo` (CRUD, merge, attach/detach, counts)
- `chunks_repo.py` — `ChunksRepo`
- `vectors_repo.py` — `VectorsRepo` (insert/knn em `vec_chunks`)
- `summaries_repo.py` — `SummariesRepo` (upsert/knn em `vec_summaries`)
- `settings_repo.py` — `SettingsRepo` (KV runtime config)
- `bookmarks_repo.py`, `progress_repo.py` — bookmarks e progresso

`db.py` abre a conexão com sqlite-vec carregado, FK `ON`, WAL, e a
envolve em `LockedConnection` (thread-safe p/ o threadpool do FastAPI).
