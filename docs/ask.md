# LLM — descrição, recomendação e tags

→ [overview.md](overview.md) | [database.md](database.md) | [api.md](api.md)

As features LLM são opcionais. Ligam quando `LABOOKE_LLM_BASE_URL`
**e** `LABOOKE_LLM_MODEL` estão definidos; caso contrário os endpoints
respondem `503 llm_unavailable`.

## Config (env vars)

| Var                          | Default | O que faz                                  |
|------------------------------|---------|---------------------------------------------|
| `LABOOKE_LLM_BASE_URL`       | *(vazio)* | Base OpenAI-compatible do servidor LLM |
| `LABOOKE_LLM_MODEL`          | *(vazio)* | Nome do modelo (ex `gemma4-e2b-ctx16k:latest`) |
| `LABOOKE_LLM_API_KEY`        | *(vazio)* | Chave; Ollama ignora (qualquer string serve) |
| `LABOOKE_LLM_SUMMARY_PAGES`  | 10     | Quantas páginas iniciais o LLM lê p/ resumir |
| `LABOOKE_LLM_RAG_K`          | 10     | Quantos resumos o RAG recupera antes de perguntar |
| `LABOOKE_LLM_AUTO_SUMMARIZE` | false  | (reservado) resumir automaticamente na ingestão |

`LABOOKE_LLM_SUMMARY_PAGES` é o default; a página Admin pode sobrescrever
em runtime (tabela `settings`). Cliente:
`packages/core/src/labooke_core/llm/client.py` — transporte `urllib`
(sem dependência), fala `/v1/chat/completions`. Ollama não exige auth
local — ver [decisão 0007](../decisions/0007-no-hardcoded-endpoints.md).

## 1. Descrição do livro (`SummarizeService`)

`POST /api/books/{id}/summarize` (síncrono) ou em lote no Admin:

1. Extrai as primeiras N páginas do arquivo (N configurável no Admin).
2. Pede ao LLM um JSON `{author, summary}`.
3. Grava `books.author` e `books.description`; ambos continuam editáveis
   na página do livro.
4. Embebe `título + description` em `vec_summaries`, o índice leve do
   catálogo usado somente para recomendar livros.

### Lote no Admin
| Endpoint | O que faz |
|---|---|
| `POST /api/admin/summaries/invalidate` | Apaga descrições + vetores de catálogo |
| `POST /api/admin/summaries/random` `{count, pages?}` | Sorteia `count` livros sem resumo e agenda em background |
| `POST /api/admin/summaries/batch` `{book_ids, pages?}` | Agenda os ids explícitos em background |
| `PUT /api/admin/config` `{llm_summary_pages}` | Sobrescreve as páginas do resumo em runtime |
| `POST /api/admin/tags/auto` `{book_ids}` | Classifica descrições usando somente tags existentes |

## 2. Recomendação de livros (`AskService`)

`POST /api/ask` com `{"question": "..."}`:

1. **Expande**: o LLM transforma o pedido em 2–4 queries curtas; o pedido
   original também participa como fallback.
2. **Recupera**: embebe as queries e roda KNN em `vec_summaries`, que contém
   somente `título + description`.
3. **Combina**: soma os ranks das queries e limita ao top-K do catálogo.
4. **Reranqueia**: o LLM recebe o pedido e as descrições completas dos
   candidatos; devolve até cinco livros, em ordem, cada um com um motivo.

Esse fluxo não lê chunks nem o conteúdo integral dos arquivos. A aba
**Semantic** e `bible search` usam a busca híbrida de trechos em `vec_chunks`
+ BM25, descrita em [search.md](search.md).

## 3. Tags automáticas (`AutoTagService`)

O Admin envia livros já descritos em background. Para cada livro, o LLM
recebe `title`, a `description` e o vocabulário atual de tags. A resposta é
validada contra os IDs existentes; o serviço apenas anexa tags válidas e
nunca cria, renomeia ou remove tags.

## Arquivos

- `services/summarize_service.py` — `SummarizeService`
- `services/ask_service.py` — `AskService`, `AskAnswer`
- `services/auto_tag_service.py` — `AutoTagService`
- `prompts/` — um módulo por tipo de prompt LLM
- `store/summaries_repo.py` — `SummariesRepo` (vec_summaries)
- `store/settings_repo.py` — `SettingsRepo` (runtime config)
- `routes/llm.py` — endpoints `summarize` e `ask`
- `routes/admin.py` — lotes de resumos/tags + config
- `schemas/ask.py` — `AskRequest` / `AskResponse`
