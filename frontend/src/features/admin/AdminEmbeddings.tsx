import { useMemo } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { reembedBatch } from "../../api/admin";
import type { BookOut } from "../../api/books";
import { useBooks } from "../library/hooks/useBooks";
import { AdminBookChecklist } from "./AdminBookChecklist";
import { embeddingMark } from "./bookMarks";
import { useBookSelection } from "./hooks/useBookSelection";
import styles from "./AdminPage.module.css";

function failureReason(book: BookOut): string | null {
  return book.status === "failed" ? book.ingest_error : null;
}

/** Per-book embedding state, with a re-embed for just the marked books. */
export function AdminEmbeddings() {
  const queryClient = useQueryClient();
  const selection = useBookSelection();
  // useBooks already polls while any book is pending or re-embedding.
  const booksQuery = useBooks({});
  const books = useMemo(() => booksQuery.data?.items ?? [], [booksQuery.data]);

  const reembed = useMutation({
    mutationFn: () => reembedBatch([...selection.selected]),
    onSuccess: () => {
      selection.clear();
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });
  const started = reembed.data?.length ?? 0;

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Embeddings por livro</h2>
      <p className={styles.desc}>
        ✓ pronto para busca, ✗ falhou (o motivo aparece ao lado), ⟳ processando. Os marcados são
        refeitos um de cada vez no servidor.
      </p>
      <AdminBookChecklist
        books={books}
        selection={selection}
        markOf={embeddingMark}
        selectMissingLabel="Marcar sem embedding"
        detailOf={failureReason}
      >
        <button
          type="button"
          className={styles.btn}
          onClick={() => reembed.mutate()}
          disabled={reembed.isPending || selection.selected.size === 0}
        >
          {reembed.isPending ? "Enviando…" : `Re-embedar marcados (${selection.selected.size})`}
        </button>
      </AdminBookChecklist>
      {reembed.isSuccess && (
        <p className={styles.result}>
          Re-embedding iniciado para {started} livro{started !== 1 ? "s" : ""}.
        </p>
      )}
      {reembed.isError && <p className={styles.error}>{reembed.error?.message ?? "Falhou."}</p>}
    </div>
  );
}
