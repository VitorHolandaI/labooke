import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { autoTagBatch } from "../../api/admin";
import type { BookOut } from "../../api/books";
import { useBooks } from "../library/hooks/useBooks";
import { AdminBookChecklist } from "./AdminBookChecklist";
import { autoTagMark } from "./bookMarks";
import { useConfig } from "./hooks/useAdmin";
import { useBookSelection } from "./hooks/useBookSelection";
import { useBooksRefresh } from "./hooks/useBooksRefresh";
import styles from "./AdminPage.module.css";

function tagNames(book: BookOut): string | null {
  return book.tags.length > 0 ? book.tags.map((tag) => tag.name).join(", ") : null;
}

/** Which books the LLM already classified, and a run for the marked ones. */
export function AdminAutoTags() {
  const config = useConfig();
  const selection = useBookSelection();
  const [sentIds, setSentIds] = useState<readonly number[]>([]);
  const booksQuery = useBooks({});
  const books = useMemo(() => booksQuery.data?.items ?? [], [booksQuery.data]);

  const marked = books.filter((book) => selection.selected.has(book.id));
  const taggableIds = marked.filter((book) => book.description).map((book) => book.id);
  const skipped = marked.length - taggableIds.length;
  // Stop refreshing once every sent book carries its auto-tag mark.
  const waiting = books.some((book) => sentIds.includes(book.id) && !book.auto_tagged_at);
  useBooksRefresh(waiting);

  const autoTag = useMutation({
    mutationFn: () => autoTagBatch(taggableIds),
    onSuccess: (data) => {
      setSentIds(data.book_ids);
      selection.clear();
    },
  });

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Tags (LLM)</h2>
      <p className={styles.desc}>
        ✓ já classificado pelo LLM, mesmo quando nenhuma tag serviu. Usa o resumo do livro e só tags
        existentes, então livros sem resumo ficam de fora.
      </p>
      <AdminBookChecklist
        books={books}
        selection={selection}
        markOf={autoTagMark}
        selectMissingLabel="Marcar sem tag IA"
        detailOf={tagNames}
      >
        <button
          type="button"
          className={styles.btn}
          onClick={() => autoTag.mutate()}
          disabled={autoTag.isPending || taggableIds.length === 0 || !config.data?.llm_enabled}
        >
          {autoTag.isPending ? "Enviando…" : `Taguear marcados (${taggableIds.length})`}
        </button>
      </AdminBookChecklist>
      {skipped > 0 && (
        <p className={styles.result}>
          {skipped} marcado{skipped !== 1 ? "s" : ""} sem resumo, fica{skipped !== 1 ? "m" : ""} de
          fora.
        </p>
      )}
      {waiting && (
        <p className={styles.result}>
          Tagueamento iniciado no servidor. A lista atualiza automaticamente.
        </p>
      )}
      {autoTag.isError && <p className={styles.error}>{autoTag.error?.message ?? "Falhou."}</p>}
    </div>
  );
}
