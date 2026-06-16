# Ideias Futuras

Ideias maiores que valem discussão antes de implementar.

---

## Escalonamento horizontal do ingest

- [ ] **Fila de ingestão com múltiplos workers**

  Hoje o ingest roda como background task direto no FastAPI com SQLite como
  storage. SQLite não suporta múltiplos escritores simultâneos — dois workers
  tentando ingestar ao mesmo tempo travam um no outro.

  Para escalar (ex: processar centenas de livros em paralelo):

  ```
  hoje:       FastAPI → background task → SQLite

  escalável:  FastAPI → fila (Redis / RabbitMQ)
                          → worker 1  ─┐
                          → worker 2  ─┼→ PostgreSQL + pgvector
                          → worker N  ─┘
  ```

  - **Fila:** Redis (simples) ou RabbitMQ (mais robusto)
  - **Workers:** containers independentes que consomem jobs da fila
  - **Storage:** PostgreSQL + pgvector substitui SQLite + sqlite-vec
  - **Load balancer:** nginx com `upstream` apontando para N pods da API

  Faz sentido quando a biblioteca for grande o suficiente para o ingest
  sequencial ser um gargalo real.

---

## Busca orientada por LLM (book profile)

- [ ] **Geração de perfil do livro via LLM pequeno**

  Na ingestão, um LLM pequeno (ex: Gemma 2B, Phi-3 mini, LLaMA 3.2 1B) lê as
  primeiras páginas do livro — capa, prefácio, sumário, glossário — e gera um
  perfil estruturado:
  - assuntos principais
  - público-alvo
  - tecnologias / ferramentas mencionadas
  - nível (iniciante, intermediário, avançado)
  - resumo em 2–3 frases

  Esse perfil fica salvo no banco junto com os metadados do livro.

- [ ] **Nova estratégia de busca: "profile match"**

  Quando o usuário perguntar "quero um livro sobre Java para iniciantes", o
  mesmo LLM (ou um ainda menor) interpreta a query e compara com os perfis
  salvos, retornando os livros mais aderentes — sem precisar de vector search
  nos chunks.

  Flags propostas para o `bible search` / API:
  - `--semantic` — busca vetorial nos chunks (comportamento atual)
  - `--lexical` — LIKE no título/filename (comportamento atual)
  - `--hybrid` — RRF de semantic + lexical (comportamento atual do testes_arquitetura)
  - `--profile` — match via perfil LLM (nova estratégia)
  - default sugerido: `--profile` (mais natural para perguntas sobre o livro)

- [ ] **Cache de Q&A classificadas**

  Perguntas já feitas + qual livro foi escolhido → dataset de preferência.
  O modelo pode consultar esse histórico para ranquear melhor em queries
  parecidas. Com volume suficiente, pode virar fine-tuning do modelo de perfil.

- [ ] **Considerações de RAM / latência**

  - Geração de perfil: roda só na ingestão, pode ser lento (offline OK).
  - Busca por perfil: modelo precisa ficar em memória ou usar idle-shutdown
    igual ao worker de embeddings atual. Ver `LABOOKE_EMBED_WORKER_IDLE_SECONDS`.
  - Alternativa leve: usar o próprio modelo de embeddings atual para embeddar
    o perfil em vez de rodar LLM na busca — trade-off qualidade × RAM.
