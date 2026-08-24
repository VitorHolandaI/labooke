# LLM — resumo e "pergunte à biblioteca"

→ [overview.md](overview.md) | [database.md](database.md) | [api.md](api.md)

Duas features LLM, ambas opcionais. Ligam quando `LABOOKE_LLM_BASE_URL`
**e** `LABOOKE_LLM_MODEL` estão definidos; caso contrário os endpoints
respondem `503 llm_unavailable`.

## Config (env vars)

| Var                          | Default | O que faz                                  |
|------------------------------|---------|---------------------------------------------|
| `LABOOKE_LLM_BASE_URL`       | *(vazio)* | Base OpenAI-compatible (ex `http://10.66.66.15:11434/v1` p/ Ollama) |
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

## 1. Resumo do livro (`SummarizeService`) — DOIS textos

`POST /api/books/{id}/summarize` (síncrono) ou em lote no Admin:

1. Extrai as primeiras N páginas do arquivo (N configurável no Admin).
2. Pede ao LLM um JSON `{author, summary, rag_summary}`.
3. Grava `books.description` (resumo legível p/ UI) e `books.rag_text`
   (texto keyword-rich focado em recuperação).
4. Embebe **o `rag_text`** em `vec_summaries` — a busca semântica usa
   esse texto, não o resumo de exibição.

### Lote no Admin
| Endpoint | O que faz |
|---|---|
| `POST /api/admin/summaries/invalidate` | Apaga descrição + rag_text + vetores de todos |
| `POST /api/admin/summaries/random` `{count, pages?}` | Sorteia `count` livros sem resumo e agenda em background |
| `POST /api/admin/summaries/batch` `{book_ids, pages?}` | Agenda os ids explícitos em background |
| `PUT /api/admin/config` `{llm_summary_pages}` | Sobrescreve as páginas do resumo em runtime |

## 2. Pergunte à biblioteca (`AskService`) — RAG

`POST /api/ask` com `{"question": "..."}`:

1. **Reformula**: o LLM transforma a pergunta natural numa query curta.
2. **Recupera**: embebe a query e roda KNN em `vec_summaries` (embeddings
   do `rag_text`) → top-K.
3. **Responde**: o LLM recebe `{pergunta + resumos top-K}` e devolve a
   recomendação em prosa + a lista de livros candidatos.

Falha na reformulação cai de volta para a pergunta crua; o retrieval
continua funcionando. O `bible search` (sem `--lexical`) chama esse
endpoint — ver [bible.md](bible.md).

## Arquivos

- `services/summarize_service.py` — `SummarizeService`
- `services/ask_service.py` — `AskService`, `AskAnswer`
- `store/summaries_repo.py` — `SummariesRepo` (vec_summaries)
- `store/settings_repo.py` — `SettingsRepo` (runtime config)
- `routes/llm.py` — endpoints `summarize` e `ask`
- `routes/admin.py` — lote de resumos + config
- `schemas/ask.py` — `AskRequest` / `AskResponse`
