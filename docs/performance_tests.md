# Testes de performance — busca semântica vs. escala de PDFs

Objetivo: demonstrar empiricamente como o tempo de busca cresce conforme o número
de PDFs (e, portanto, de chunks/embeddings) aumenta, e em que ponto cada algoritmo
de pesquisa passa a ser mais eficiente. A hipótese é que o brute-force exato
(atual) cresce linear com o corpus, enquanto índices ANN (HNSW/IVF) crescem
sublinear e vencem a partir de um certo limiar.

---

## 1. Endpoint sob teste

```
GET /api/search?q=<query>&mode=semantic&algo=<algo>&k=10
```

O parâmetro `algo` seleciona a implementação de KNN por trás do `VectorsRepo`.
Todas recebem o mesmo vetor de query (E5 `query:`-prefixed, 384 dims) e devem
retornar `(chunk_id, distance)` ordenado — só muda a estratégia interna.

```python
# placeholders — mesma interface, implementações diferentes
class KnnBackend(Protocol):
    def knn(self, query: list[float], k: int, book_ids: list[int]) -> list[tuple[int, float]]: ...

BACKENDS = {
    "brute":  BruteForceKnn(),   # atual — sqlite-vec, scan O(C × 384)
    "hnsw":   HnswKnn(),         # placeholder — hnswlib, grafo em camadas
    "ivf":    IvfKnn(),          # placeholder — FAISS IVF, clusters Voronoi
    "pq":     IvfPqKnn(),        # placeholder — IVF + product quantization
    "twostage": TwoStageKnn(),   # placeholder — BM25 filtra N, KNN refina
}
```

> Os backends `hnsw`/`ivf`/`pq`/`twostage` são *placeholders* a implementar.
> O `brute` já existe (`packages/core/.../vectors_repo.py`).

---

## 2. Eixo de escala (variável independente)

Gerar corpora sintéticos com tamanhos crescentes. Cada PDF ≈ 200 páginas ≈ 200 chunks.

| Nível | PDFs | Chunks (C) | Embeddings em RAM (float32) |
|------:|-----:|-----------:|----------------------------:|
| S     |   10 |      2 000 | ~3 MB                       |
| M     |  100 |     20 000 | ~30 MB                      |
| L     | 1 000 |    200 000 | ~300 MB                     |
| XL    | 10 000 |  2 000 000 | ~3 GB                       |

Para isolar o algoritmo, usar embeddings aleatórios normalizados (não precisa
re-embedar PDFs reais) — o custo do produto interno é o mesmo.

---

## 3. Métricas a coletar

Por (algoritmo × nível de escala):

- **Latência** p50, p95, p99 de uma única query (ms)
- **Throughput** (queries/seg) com 1 e com N threads concorrentes
- **Recall@10** — fração do top-10 do ANN que bate com o top-10 do `brute` (ground truth)
- **Memória** residente do índice (MB)
- **Tempo de build** do índice (s) — relevante para ingestão/re-embed

---

## 4. Casos de teste

### CT-1 — Escala de latência (o gráfico principal)
Para cada `algo`, rodar 200 queries em cada nível S→XL e plotar **latência p95 × C**.
- Esperado: `brute` cresce linear; `hnsw`/`ivf` quase plano (log).
- **Demonstra o ponto de cruzamento** onde o ANN passa a vencer.

### CT-2 — Precisão vs. velocidade (tradeoff do `ef`)
Fixar nível L. Para `hnsw`, varrer `efSearch ∈ {10, 50, 100, 200, 400}`.
- Plotar **recall@10 × latência**.
- Esperado: curva côncava — ganho de recall satura, latência sobe linear.

### CT-3 — Concorrência (lembrar do bug do LockedConnection)
Nível M. Disparar 1, 4, 16, 64 queries concorrentes.
- Medir throughput e verificar que não há `InterfaceError` no SQLite.
- Esperado: `brute` serializa no lock; ANN em memória escala melhor com threads.

### CT-4 — Filtro de tags reduz C
Nível L, com whitelist de `book_ids` cobrindo 1%, 10%, 100% do corpus.
- Esperado: `brute` cai proporcional ao filtro (C menor); ANN ganha menos
  (índice global, filtro é pós-processamento) — pode até perder em filtros agressivos.

### CT-5 — Two-stage vs. ANN puro
Nível L/XL. Comparar `twostage` (BM25 top-200 → brute nos 200) contra `hnsw`.
- Medir latência e recall@10.
- Esperado: `twostage` é simples e barato quando a query tem keywords fortes;
  perde recall em queries puramente conceituais sem termos exatos.

### CT-6 — Custo de build / ingestão
Para cada `algo`, medir tempo de construir o índice nos níveis S→XL.
- Esperado: `brute` ≈ 0 (sem índice); `hnsw` é o mais caro de construir.
- Trade-off: paga-se na ingestão para economizar na busca.

### CT-7 — Memória
Registrar RSS do índice em cada nível.
- Esperado: `brute` e `hnsw` guardam vetores full (float32); `pq` comprime
  ~4–8× com perda de recall.

---

## 5. Metodologia

- Hardware fixo (mesmo container, `cpus: 1.5`, `memory: 2g` do `docker-compose.yml`).
- Warm-up: descartar as 20 primeiras queries (carga de modelo/índice em cache).
- Cada medição = mediana de ≥ 200 queries com vetores de query distintos.
- Isolar a busca: medir só o `knn()`, fora do encode da query e da hidratação de snippets.
- `brute` é o **ground truth** para recall dos demais.
- Repetir 3 execuções; reportar média ± desvio.

---

## 6. Critério de sucesso (o que o teste deve provar)

1. Existe um **C de cruzamento** acima do qual `hnsw`/`ivf` < `brute` em latência.
2. Abaixo desse C, o `brute` exato é competitivo e dispensa a complexidade de ANN.
3. O ganho de ANN vem com **custo de recall** mensurável (não é grátis).
4. Para o tamanho atual da biblioteca (~nível S), `brute` é suficiente — a migração
   só se justifica projetando crescimento até nível L+.

---

## 7. Esboço do harness

```python
import time, statistics

def bench(backend, queries, k=10):
    lat = []
    for q in queries:
        t0 = time.perf_counter()
        backend.knn(q, k=k, book_ids=ALL)
        lat.append((time.perf_counter() - t0) * 1000)
    return {
        "p50": statistics.median(lat),
        "p95": statistics.quantiles(lat, n=20)[18],
        "p99": statistics.quantiles(lat, n=100)[98],
    }

for level, vectors in CORPORA.items():      # S, M, L, XL
    for name, backend in BACKENDS.items():
        backend.build(vectors)
        print(level, name, bench(backend, QUERIES))
```

Saída sugerida: CSV `(algo, level, C, p50, p95, recall, mem_mb, build_s)` →
plotar latência × C (CT-1) e recall × latência (CT-2).
