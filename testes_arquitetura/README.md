# testes_arquitetura

Lab para explorar e comparar diferentes estratégias de retrieval.
Precisa do servidor rodando em `http://localhost:8000`.

## Uso

```bash
# da raiz do repositório
PYTHONPATH=. uv run python testes_arquitetura/run.py "design patterns" --k 5

# retriever específico
PYTHONPATH=. uv run python testes_arquitetura/run.py "concorrência" --retriever hybrid

# comparar todos
PYTHONPATH=. uv run python testes_arquitetura/run.py "codigo limpo" --retriever all
```

## Retrievers disponíveis

| Nome | Arquivo | Descrição |
|---|---|---|
| `semantic` | `via_api.py` | KNN semântico via HTTP API (baseline atual) |
| `lexical` | `via_api.py` | Busca por título via HTTP API |
| `hybrid` | `hybrid.py` | Lexical + semântico fundidos com RRF |
| `cross_encoder` | `cross_encoder.py` | Semântico + rerank com cross-encoder |

## Adicionar um novo retriever

1. Criar arquivo novo (ex: `bm25.py`)
2. Herdar de `Retriever` em `base.py` e implementar `search()`
3. Registrar em `run.py` no dict `_RETRIEVERS`

## Cross-encoder

Requer `sentence-transformers` instalado. Modelo padrão: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~85 MB, baixado automaticamente).
Mais lento que semântico puro, mas geralmente mais preciso.

→ Ver [docs/search.md](../docs/search.md) para arquitetura do sistema atual.
