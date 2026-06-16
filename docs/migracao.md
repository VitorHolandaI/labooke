# Migração e recuperação

→ [overview.md](overview.md) | [docker.md](docker.md)

## O que fica onde

| Dado | Onde | Perde se... |
|---|---|---|
| Arquivo do livro (PDF/EPUB/TXT) | `data/books/` | deletar o arquivo |
| Título, autor, formato | `library.db` | deletar o registro |
| Tags associadas | `library.db` | deletar o registro |
| Embeddings / chunks | `library.db` | deletar o registro ou reembeddar |
| Bookmarks | `library.db` | deletar o registro |
| Progresso de leitura | `library.db` | deletar o registro |
| Covers (thumbnails) | `data/covers/` | deletar o arquivo de cover |
| Modelo de embeddings | volume `models` | deletar o volume |

---

## Atualizar container (sem perder dados)

Volumes persistem entre `down/up`. Pode fazer à vontade:

```bash
git pull
docker compose down
docker compose up --build -d
```

> **Nunca use `docker compose down -v`** — isso apaga os volumes e perde tudo.

---

## Migrar para outro servidor

```bash
# 1. no servidor atual — para e copia os dados
docker compose down
tar czf labooke-data.tar.gz data/

# 2. transfere para o novo servidor
scp labooke-data.tar.gz usuario@novo-servidor:~/

# 3. no novo servidor
git clone --recurse-submodules http://<git-host>:<git-port>/<org>/<repo>.git
cd labooke
cp .env.example .env
tar xzf ~/labooke-data.tar.gz
docker compose up --build -d
```

O modelo de embeddings (`models` volume) vai ser baixado novamente na primeira busca semântica (~130 MB). Se quiser evitar o download, copie o volume também:

```bash
# no servidor atual
docker run --rm -v labooke_models:/data -v $(pwd):/backup \
  alpine tar czf /backup/labooke-models.tar.gz -C /data .

# no novo servidor (antes do docker compose up)
docker volume create labooke_models
docker run --rm -v labooke_models:/data -v $(pwd):/backup \
  alpine tar xzf /backup/labooke-models.tar.gz -C /data
```

---

## Recuperar livro com metadados deletados

Se o arquivo ainda está em `data/books/` mas o registro sumiu do banco:

```bash
# move o arquivo para inbox e dispara scan
mv data/books/<sha256>.pdf data/inbox/
# Admin → Scan now  (ou)
bible scan
```

O scan re-ingesta e recria metadados, chunks e embeddings.  
**Perde:** título customizado, tags, bookmarks e progresso de leitura.  
**Mantém:** arquivo original intacto.

---

## Mudar modelo de embeddings

Trocar `LABOOKE_EMBED_MODEL` no `.env` invalida todos os embeddings existentes
(dimensões ou espaço vetorial diferente). Após trocar:

1. Atualiza `.env`
2. `docker compose down && docker compose up --build -d`
3. Admin → **Redo all embeddings** (reprocessa todos os livros)

> Isso pode demorar bastante dependendo do tamanho da biblioteca.

---

## Mudar CHUNK_PAGES

Mudar `LABOOKE_CHUNK_PAGES` não quebra nada imediatamente, mas os livros
antigos ficam com chunking diferente dos novos. Para normalizar:

Admin → **Redo all embeddings**

---

## Backup mínimo

Só o `data/` é suficiente para restaurar tudo (exceto o modelo):

```bash
# backup
docker compose down
cp -r data/ data.bak/
docker compose up -d

# restore
docker compose down
rm -rf data/
cp -r data.bak/ data/
docker compose up -d
```
