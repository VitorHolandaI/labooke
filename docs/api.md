# API HTTP

→ [overview.md](overview.md) | [running.md](running.md)

Docs interativas (Swagger): `http://localhost:8000/docs`

## Endpoints principais

### Livros
| Método | Rota                    | Descrição                          |
|--------|-------------------------|------------------------------------|
| GET    | `/api/books`            | Lista livros (suporta filtros)     |
| POST   | `/api/books`            | Upload (multipart, 202 + background)|
| GET    | `/api/books/{id}`       | Detalhe de um livro                |
| DELETE | `/api/books/{id}`       | Remove livro + arquivo             |
| GET    | `/api/books/{id}/file`  | Serve o arquivo original           |

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

### Admin
| Método | Rota                  | Descrição                            |
|--------|-----------------------|--------------------------------------|
| POST   | `/api/admin/scan`     | Escaneia pasta inbox e ingere        |
| POST   | `/api/admin/reindex/{id}` | Re-ingere um livro              |

`GET /healthz` — healthcheck (usado pelo Docker).
