# API HTTP

→ [overview.md](overview.md) | [running.md](running.md) | [ask.md](ask.md) | [database.md](database.md)

Docs interativas (Swagger): `http://localhost:8000/docs`

## Endpoints principais

### Livros
| Método | Rota                    | Descrição                          |
|--------|-------------------------|------------------------------------|
| GET    | `/api/books`            | Lista livros (filtros + `sort=recent`) |
| POST   | `/api/books`            | Upload (multipart, 202 + background)|
| GET    | `/api/books/{id}`       | Detalhe de um livro                |
| PATCH  | `/api/books/{id}`       | Edita `title` / `author` / `description` |
| DELETE | `/api/books/{id}`       | Remove livro + arquivo             |
| GET    | `/api/books/{id}/file`  | Serve o arquivo original           |

`GET /api/books?sort=recent` ordena por última leitura (mais recente
primeiro), usando `reading_progress.updated_at`.

### Tags
| Método | Rota                    | Descrição                          |
|--------|-------------------------|------------------------------------|
| GET    | `/api/tags`             | Lista tags com contagem de livros  |
| POST   | `/api/tags`             | Cria tag (201; 409 se slug existe) |
| PATCH  | `/api/tags/{id}`        | Renomeia / recolore                |
| DELETE | `/api/tags/{id}`        | Remove tag e vínculos              |
| POST   | `/api/tags/merge`       | Merge de duas tags                 |

### Busca, Bookmarks, Progresso
| Método | Rota                              | Descrição                   |
|--------|-----------------------------------|-----------------------------|
| GET    | `/api/search`                     | Busca (ver [search.md](search.md)) |
| GET    | `/api/books/{id}/bookmarks`       | Lista bookmarks             |
| POST   | `/api/books/{id}/bookmarks`       | Cria bookmark               |
| PATCH  | `/api/bookmarks/{id}/note`        | Edita nota                  |
| DELETE | `/api/bookmarks/{id}`             | Remove bookmark             |
| GET    | `/api/books/{id}/progress`        | Lê progresso                |
| PUT    | `/api/books/{id}/progress`        | Salva progresso             |

### LLM (ver [ask.md](ask.md))
| Método | Rota                              | Descrição                     |
|--------|-----------------------------------|-------------------------------|
| POST   | `/api/books/{id}/summarize`       | Gera resumo via LLM (síncrono)|
| POST   | `/api/ask`                        | Pergunta em linguagem natural |

Ambos retornam `503 llm_unavailable` se o LLM não estiver configurado.

### Admin (resumos em lote + config)
| Método | Rota                              | Descrição                          |
|--------|-----------------------------------|------------------------------------|
| POST   | `/api/admin/summaries/invalidate` | Apaga descrições e vetores de catálogo |
| POST   | `/api/admin/summaries/random`     | Sorteia N sem resumo e agenda (202) |
| POST   | `/api/admin/summaries/batch`      | Agenda ids explícitos (202)         |
| POST   | `/api/admin/tags/auto`            | Tagueia descrições com tags existentes (202) |
| PUT    | `/api/admin/config`               | Sobrescreve `llm_summary_pages`     |

### Admin
| Método | Rota                  | Descrição                            |
|--------|-----------------------|--------------------------------------|
| POST   | `/api/admin/scan`     | Escaneia pasta inbox e ingere        |
| POST   | `/api/admin/reembed-all` | Re-embebe todos os livros         |

`GET /healthz` — healthcheck (usado pelo Docker).
