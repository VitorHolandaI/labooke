# Modelos de domínio

→ [overview.md](overview.md) | [database.md](database.md)

Modelos Pydantic puros, sem I/O, SQL ou framework. Ficam em
`packages/core/src/labooke_core/domain/models.py`. Repositórios e
services mapeiam entre esses tipos e o storage/HTTP.

| Modelo            | Campos-chave                                                            | Onde nasce      |
|-------------------|-------------------------------------------------------------------------|-----------------|
| `Book`            | `id`, `sha256`, `path`, `title`, `author`, `description`, `format`, `page_count`, `status`, `ingest_error`, `tags` | ingest           |
| `BookStatus`      | enum `pending \| ready \| reembedding \| failed`                        | ingest           |
| `Tag`             | `id`, `name`, `slug`, `color`                                           | tags page       |
| `Chunk`           | `id`, `book_id`, `page_start`, `page_end`, `text`                       | pipeline embed  |
| `SearchHit`       | `book_id`, `page_start`, `page_end`, `snippet`, `score`                 | search          |
| `Bookmark`        | `id`, `book_id`, `page_no`, `label`, `note`                             | reader          |
| `ReadingProgress` | `book_id`, `page_no`, `updated_at`                                      | reader          |
| `PageText`        | `page_no`, `text` (transiente, nunca persistido)                        | extractors      |

## `Book.description`

Adicionado na migration `0004` (ver [database.md](database.md)). Texto
curto do resumo do livro, gerado pelo LLM (`SummarizeService`) lendo as
primeiras `LABOOKE_LLM_SUMMARY_PAGES` páginas. Usado pelo `AskService`
como base do RAG de perguntas. `author` já existia desde `0001`.

## Notas de design

- O arquivo original é a fonte de verdade do texto — o DB guarda só
  metadados + chunks + embeddings. Ver
  [decisão 0001](../decisions/0001-storage-no-text-in-db.md).
- `Book.require_path()` levanta `FileNotFoundError` se não houver arquivo,
  forçando os serviços de leitura a lidar com livro sem fonte.
- Modelos não carregam tags por padrão; `LibraryService._with_tags`
  hidrata `book.tags` via `TagsRepo.for_book`.
