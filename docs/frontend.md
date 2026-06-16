# Frontend

→ [overview.md](overview.md) | [running.md](running.md) | [api.md](api.md)

## Estrutura

```
frontend/src/
├── api/          # clientes HTTP (fetch wrapper tipado)
├── features/
│   ├── library/  # UploadDropzone, BookCard, filtros, busca
│   └── reader/   # viewers (PDF/EPUB/TXT), BookmarkDrawer, hooks
├── routes/       # LibraryPage, ReaderPage, TagsPage, AdminPage
└── theme/        # dark/light mode (CSS custom properties)
```

## Rotas

| URL           | Página       | Descrição                          |
|---------------|--------------|------------------------------------|
| `/`           | LibraryPage  | Grid de livros, upload, busca, tags|
| `/read/:id`   | ReaderPage   | Leitor + sidebar de bookmarks      |
| `/tags`       | TagsPage     | CRUD de tags, merge                |
| `/admin`      | AdminPage    | Scan de pasta, re-ingest           |

## Tecnologias

- **TanStack Query** — cache de dados, mutations, invalidação automática
- **CSS Modules** — escopo local, sem Tailwind ([ADR 0010](../decisions/0010-css-modules-no-tailwind.md))
- **msw** — mock de API nos testes (Vitest + Testing Library)
- **React Router v6** — roteamento SPA com fallback nginx

## Tipagem da API

`src/api/openapi.ts` é gerado do schema OpenAPI do backend.  
Tipos do `client.ts` garantem que o frontend fica em sincronia com a API.

## Testes

```bash
cd frontend && npx vitest run   # 23 suites, ~83 testes
```

Cobrem upload (staging, progresso, rejeição), bookmarks, progresso e busca.  
→ Ver [reader.md](reader.md) para detalhes do tela cheia / double page.
