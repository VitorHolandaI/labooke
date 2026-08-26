# Performance da busca

## Complexidades por modo

| Modo | Complexidade | Gargalo |
|---|---|---|
| Lexical | O(n) | varre todos os n livros |
| BM25 / FTS5 | O(log V + P) | P = docs que contêm o termo |
| Semântico (KNN exato) | O(C × 1024) | C = total de chunks na whitelist |
| Híbrido | O(C × 1024 + P) | dominado pelo semântico |

**V** = tamanho do vocabulário, **P** = posting list do termo, **C** = chunks elegíveis.

## Pior caso do KNN

O top-k não reduz o trabalho de computação — só reduz memória (heap de k elementos).
No pior caso o chunk mais próximo é o último calculado, então todos os C × 1024
produtos internos são inevitáveis. Com filtro de tags, C cai para os chunks dos
livros que passaram o filtro.

Estimativa atual (~45 livros, ~9 k chunks): ~3,4 M multiplicações por busca → < 100 ms.

## Por que BM25 pode ser mais rápido

Com índice invertido e algoritmos de early stopping (ex: WAND), é possível provar
que documentos restantes na posting list não superam o k-ésimo resultado já encontrado
e parar antes de pontuar todos os P documentos. O SQLite FTS5 não implementa WAND,
mas o `LIMIT` aplicado sobre o resultado ranqueado evita retornar mais do necessário.

## Mitigações se a biblioteca crescer muito

1. **Filtro de metadados** — já implementado via `book_ids` por tags. Reduz C diretamente.
2. **Two-stage retrieval** — BM25 retorna N candidatos (~100), KNN roda só nesses N.
   Estrutura já existe para isso (hybrid RRF).
3. **ANN index** — HNSW ou IVF trocam exatidão garantida por O(log C). Requer migrar
   de sqlite-vec para pgvector ou Qdrant.
4. **Quantização** — comprimir vetores de float32 para int8 reduz memória e acelera
   produto interno com instruções SIMD. sqlite-vec tem suporte experimental.

## Limiar prático

O brute-force atual começa a ser perceptível (~> 500 ms) a partir de ~100 k chunks
(~500 livros de 200 páginas cada). Abaixo disso não justifica a complexidade de ANN.
