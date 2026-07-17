# Upload e ingestão de livros

→ [overview.md](overview.md) | [api.md](api.md)

![Upload](images/upload.png)

## Upload pela UI

1. Arraste arquivos (PDF/EPUB/TXT/MD) ou clique em **Choose files**
2. **Staging** — para cada arquivo edite o título e escolha tags
   - É possível criar uma tag nova direto nessa tela (inline)
3. Clique **Upload N files** — barra de progresso cresce de 0 → 100 %
4. Após envio: status *Ingesting…* enquanto o backend processa

## Pipeline de ingestão (backend)

```
arquivo recebido
    → sha256 dedup (ignora duplicata)
    → extrai texto por página
    → divide em chunks (LABOOKE_CHUNK_PAGES páginas por chunk)
    → gera embeddings (modelo bge-small-en-v1.5)
    → salva metadados + embeddings no SQLite
    → status book: pending → ready | failed
```

O upload retorna 202 imediatamente; a ingestão roda em background task.  
Ver [ADR 0005](../decisions/0005-background-ingest.md) e [ADR 0006](../decisions/0006-sha256-dedup.md).

## Importação por pasta

1. Coloque arquivos em `data/inbox/`
2. Admin → **Scan now**
3. Arquivos válidos são movidos para `data/books/` e ingeridos

## Re-ingestão

Admin → **Redo** em um livro reprocessa texto + embeddings  
(útil após mudar `LABOOKE_CHUNK_PAGES` ou o modelo).

→ Ver [search.md](search.md) para como os embeddings são usados na busca.
