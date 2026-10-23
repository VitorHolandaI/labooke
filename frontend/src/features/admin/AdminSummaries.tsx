import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  invalidateSummaries,
  summarizeBatch,
  summarizeRandom,
  updateConfig,
} from "../../api/admin";
import { useBooks } from "../library/hooks/useBooks";
import { ConfirmDialog } from "../library/ConfirmDialog";
import { AdminBookChecklist } from "./AdminBookChecklist";
import { summaryMark } from "./bookMarks";
import { useConfig } from "./hooks/useAdmin";
import { useBookSelection } from "./hooks/useBookSelection";
import { useBooksRefresh } from "./hooks/useBooksRefresh";
import styles from "./AdminPage.module.css";

export function AdminSummaries() {
  const config = useConfig();
  const queryClient = useQueryClient();
  const configPages = config.data?.llm_summary_pages ?? 10;
  const [pages, setPages] = useState<string | null>(null);
  const [count, setCount] = useState(5);
  const selection = useBookSelection();
  const [confirmInvalidate, setConfirmInvalidate] = useState(false);
  const [processing, setProcessing] = useState(false);

  const effectivePages = pages === null ? configPages : Number(pages) || configPages;

  const booksQuery = useBooks({});
  const books = useMemo(() => booksQuery.data?.items ?? [], [booksQuery.data]);
  const missing = useMemo(() => books.filter((b) => !b.description).length, [books]);
  useBooksRefresh(processing && missing > 0);

  const savePages = useMutation({
    mutationFn: (value: number) => updateConfig({ llm_summary_pages: value }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const invalidate = useMutation({
    mutationFn: invalidateSummaries,
    onSuccess: () => {
      selection.clear();
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });

  const random = useMutation({
    mutationFn: () => summarizeRandom(count, effectivePages),
    onSuccess: (data) => {
      selection.addIds(data.book_ids);
      setProcessing(data.book_ids.length > 0);
    },
  });

  const batch = useMutation({
    mutationFn: () => summarizeBatch([...selection.selected], effectivePages),
    onSuccess: () => setProcessing(selection.selected.size > 0),
  });

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

      <AdminBookChecklist
        books={books}
        selection={selection}
        markOf={summaryMark}
        selectMissingLabel="Marcar sem resumo"
      >
        <button
          type="button"
          className={styles.btn}
          onClick={() => batch.mutate()}
          disabled={batch.isPending || selection.selected.size === 0}
        >
          {batch.isPending ? "Enviando…" : `Resumir marcados (${selection.selected.size})`}
        </button>
        <button
          type="button"
          className={`${styles.btn} ${styles.btnDanger}`}
          onClick={() => setConfirmInvalidate(true)}
        >
          Invalidar todos
        </button>
      </AdminBookChecklist>

      {processing && missing > 0 && (
        <p className={styles.result}>
          Processando… ({missing} livro{missing !== 1 ? "s" : ""} sem resumo restante
          {missing !== 1 ? "s" : ""}). A lista atualiza sozinha.
        </p>
      )}

      {random.isError && <p className={styles.error}>{random.error?.message ?? "Falhou."}</p>}

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
