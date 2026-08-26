# Busca

→ [overview.md](overview.md) | [api.md](api.md) | [docker.md](docker.md)

![Filtro por tag](images/library-filter-tag.png)

## Modos

| Modo        | Como funciona                                      | Velocidade    |
|-------------|----------------------------------------------------|---------------|
| **Hybrid**  | KNN semântico + BM25 (FTS5) combinados via RRF     | ~200–500 ms   |
| Semântico   | KNN no sqlite-vec (vetores E5 multilingual)        | ~200–500 ms   |
| Lexical     | `LIKE` no título/filename                          | Instantâneo   |
| Tag filter  | SQL `WHERE tag IN (...)` combinado                 | Instantâneo   |

O modo padrão é **hybrid**. Os modos são ortogonais e combinam com tag filter em uma única query.  
Ver [ADR 0003](../decisions/0003-search-modes.md).

A aba **Semantic** da interface web e `bible search` usam o modo hybrid:
buscam trechos nos chunks de PDFs/EPUBs e aplicam o reranking RRF abaixo.

## Busca híbrida (padrão)

Combina dois sinais via **Reciprocal Rank Fusion (RRF)**:

1. **Semântico** — query codificada com prefixo `"query: "` → KNN nos vetores → rank por distância
2. **BM25** — FTS5 no texto dos chunks (`chunks_fts`) → rank por frequência de termos

Score final: `1/(60 + rank_semântico) + 1/(60 + rank_BM25)`

Livros bem ranqueados em ambos sobem; livros que só aparecem num dos sinais descem.  
Isso resolve o problema de modelos semânticos confundirem tópicos próximos (ex: Java vs Python).

## Modelo de embedding

- `bge-m3` — multilíngue (100+ idiomas), vetor dense nativo de 1024 dimensões
- Servido pelo Ollama em `LABOOKE_EMBED_BASE_URL`
- Configurável via `LABOOKE_EMBED_MODEL`
- O Admin pode trocar temporariamente o endpoint Ollama; `.env` é o fallback
- Sem prefixos de query/documento: BGE-M3 não os exige

## Filtro por tags

O sidebar da biblioteca mostra todas as tags. Clicar seleciona;  
a busca retorna apenas livros com **todas** as tags selecionadas (AND).  
Combina com qualquer modo de busca.

## Endpoint

```
GET /api/search?q=texto&mode=hybrid&tags=1&tags=2&tag_mode=all&k=10&group_by_book=true
```

Parâmetros: `q`, `mode` (`hybrid` | `semantic` | `lexical`), `tags`, `tag_mode`, `exclude`, `k`, `group_by_book`.  
Ver [api.md](api.md) para resposta completa.

## RAM do modelo

- Standby (sem modelo): ~200 MB
- Com worker ativo (E5 small): ~470 MB
- Após idle shutdown: ~200 MB

→ Ver [docker.md](docker.md) para endpoint Ollama e deploy.
