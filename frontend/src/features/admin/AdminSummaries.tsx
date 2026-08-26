import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  autoTagBatch,
  invalidateSummaries,
  summarizeBatch,
  summarizeRandom,
  updateConfig,
} from "../../api/admin";
import { useBooks } from "../library/hooks/useBooks";
import { ConfirmDialog } from "../library/ConfirmDialog";
import { useConfig } from "./hooks/useAdmin";
import styles from "./AdminPage.module.css";

export function AdminSummaries() {
  const config = useConfig();
  const queryClient = useQueryClient();
  const configPages = config.data?.llm_summary_pages ?? 10;
  const [pages, setPages] = useState<string | null>(null);
  const [count, setCount] = useState(5);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [confirmInvalidate, setConfirmInvalidate] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [tagging, setTagging] = useState(false);

  const effectivePages = pages === null ? configPages : Number(pages) || configPages;

  const booksQuery = useBooks({});
  const books = useMemo(() => booksQuery.data?.items ?? [], [booksQuery.data]);
  const missing = useMemo(() => books.filter((b) => !b.description).length, [books]);
  const taggableIds = useMemo(
    () => books.filter((book) => selected.has(book.id) && book.description).map((book) => book.id),
    [books, selected],
  );

  const savePages = useMutation({
    mutationFn: (value: number) => updateConfig({ llm_summary_pages: value }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const invalidate = useMutation({
    mutationFn: invalidateSummaries,
    onSuccess: () => {
      setSelected(new Set());
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });

  const random = useMutation({
    mutationFn: () => summarizeRandom(count, effectivePages),
    onSuccess: (data) => {
      setSelected((current) => new Set([...current, ...data.book_ids]));
      setProcessing(data.book_ids.length > 0);
    },
  });

  const batch = useMutation({
    mutationFn: () => summarizeBatch([...selected], effectivePages),
    onSuccess: () => setProcessing(selected.size > 0),
  });

  const autoTag = useMutation({
    mutationFn: () => autoTagBatch(taggableIds),
    onSuccess: () => setTagging(taggableIds.length > 0),
  });

  useEffect(() => {
    if ((!processing || missing === 0) && !tagging) return;
    const handle = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    }, 5000);
    return () => window.clearInterval(handle);
  }, [processing, tagging, missing, queryClient]);

  function toggle(id: number) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAll() {
    setSelected(new Set(books.map((b) => b.id)));
  }

  function clearAll() {
    setSelected(new Set());
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Resumos (LLM)</h2>
      <p className={styles.desc}>
        O LLM lê as primeiras <strong>N páginas</strong> e gera a descrição e o autor do livro. A
        descrição também alimenta a recomendação e o tagueamento, que usa somente tags existentes.
      </p>

      <div className={styles.row}>
        <label className={styles.field}>
          Páginas por resumo
          <input
            type="number"
            min={1}
            className={styles.input}
            value={pages ?? String(configPages)}
            onChange={(e) => setPages(e.target.value)}
            onBlur={() => {
              if (effectivePages !== configPages) savePages.mutate(effectivePages);
              setPages(null);
            }}
            aria-label="Páginas por resumo"
          />
        </label>
        <span className={styles.result}>{savePages.isPending ? "Salvando…" : "Salvo"}</span>
      </div>

      <div className={styles.row}>
        <label className={styles.field}>
          Quantos aleatórios
          <input
            type="number"
            min={1}
            className={styles.input}
            value={count}
            onChange={(e) => setCount(Number(e.target.value) || 1)}
            aria-label="Quantos aleatórios"
          />
        </label>
        <button
          type="button"
          className={styles.btn}
          onClick={() => random.mutate()}
          disabled={random.isPending || count < 1}
        >
          {random.isPending ? "Selecionando…" : `Resumir ${count} aleatórios`}
        </button>
      </div>

      <div className={styles.row}>
        <button type="button" className={styles.btn} onClick={selectAll}>
          Marcar todos
        </button>
        <button type="button" className={styles.btn} onClick={clearAll}>
          Desmarcar todos
        </button>
        <button
          type="button"
          className={styles.btn}
          onClick={() => batch.mutate()}
          disabled={batch.isPending || selected.size === 0}
        >
          {batch.isPending ? "Enviando…" : `Resumir marcados (${selected.size})`}
        </button>
        <button
          type="button"
          className={styles.btn}
          onClick={() => autoTag.mutate()}
          disabled={autoTag.isPending || taggableIds.length === 0 || !config.data?.llm_enabled}
        >
          {autoTag.isPending ? "Enviando…" : `Taguear com IA (${taggableIds.length})`}
        </button>
        <button
          type="button"
          className={`${styles.btn} ${styles.btnDanger}`}
          onClick={() => setConfirmInvalidate(true)}
        >
          Invalidar todos
        </button>
      </div>

      {processing && missing > 0 && (
        <p className={styles.result}>
          Processando… ({missing} livro{missing !== 1 ? "s" : ""} sem resumo restante
          {missing !== 1 ? "s" : ""}). A lista atualiza sozinha.
        </p>
      )}

      {tagging && (
        <p className={styles.result}>
          Tagueamento iniciado no servidor. A lista atualiza automaticamente.
        </p>
      )}

      {random.isError && <p className={styles.error}>{random.error?.message ?? "Falhou."}</p>}

      <ul className={styles.bookList}>
        {books.map((book) => {
          const hasSummary = Boolean(book.description);
          const checked = selected.has(book.id);
          return (
            <li key={book.id} className={styles.bookRow}>
              <label className={styles.bookLabel}>
                <input type="checkbox" checked={checked} onChange={() => toggle(book.id)} />
                <span className={hasSummary ? styles.summarized : styles.noSummary}>
                  {hasSummary ? "✓" : "✗"}
                </span>
                <span className={styles.bookTitle}>{book.title}</span>
                {book.tags.length > 0 && (
                  <span className={styles.bookTags}>
                    {book.tags.map((tag) => tag.name).join(", ")}
                  </span>
                )}
              </label>
            </li>
          );
        })}
      </ul>

      {confirmInvalidate && (
        <ConfirmDialog
          title="Invalidar todos os resumos"
          message="Apaga as descrições geradas de todos os livros. Você pode re-resumir depois em lotes."
          confirmLabel="Invalidar tudo"
          danger
          isPending={invalidate.isPending}
          onClose={() => setConfirmInvalidate(false)}
          onConfirm={() => {
            invalidate.mutate(undefined, { onSuccess: () => setConfirmInvalidate(false) });
          }}
        />
      )}
    </div>
  );
}
