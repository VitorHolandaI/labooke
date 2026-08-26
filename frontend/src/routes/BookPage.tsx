import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { coverUrl, type BookOut, type BookUpdate } from "../api/books";
import { summarizeBook } from "../api/ask";
import { ConfirmDialog } from "../features/library/ConfirmDialog";
import { RenameDialog } from "../features/library/RenameDialog";
import { TagsEditDialog } from "../features/library/TagsEditDialog";
import {
  useAttachTag,
  useDeleteBook,
  useDetachTag,
  useUpdateBook,
} from "../features/library/hooks/useBookActions";
import { useTags } from "../features/library/hooks/useTags";
import { useBook } from "../features/reader/hooks/useBook";
import { useProgress } from "../features/reader/hooks/useProgress";
import styles from "./BookPage.module.css";

type DialogKind = null | "rename" | "tags" | "delete";

function BookDetailsEditor({ book }: { book: BookOut }) {
  const [author, setAuthor] = useState(book.author ?? "");
  const [description, setDescription] = useState(book.description ?? "");
  const update = useUpdateBook();
  const queryClient = useQueryClient();
  const summarize = useMutation({
    mutationFn: (id: number) => summarizeBook(id),
    onSuccess: (updated) => {
      setAuthor(updated.author ?? "");
      setDescription(updated.description ?? "");
      void queryClient.invalidateQueries({ queryKey: ["book", book.id] });
    },
  });

  function handleSave() {
    const patch: BookUpdate = {
      author: author.trim() || null,
      description: description.trim() || null,
    };
    update.mutate({ id: book.id, ...patch });
  }

  return (
    <section className={styles.details}>
      <h2 className={styles.sectionTitle}>Detalhes</h2>
      <label className={styles.field}>
        Autor
        <input
          className={styles.input}
          value={author}
          placeholder="Sem autor"
          onChange={(e) => setAuthor(e.target.value)}
        />
      </label>
      <label className={styles.field}>
        Resumo
        <textarea
          className={styles.textarea}
          value={description}
          placeholder="Sem resumo ainda. Clique em 'Resumir com IA' para gerar."
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>
      <div className={styles.fieldActions}>
        <button
          type="button"
          className={styles.btn}
          disabled={update.isPending}
          onClick={handleSave}
        >
          {update.isPending ? "Salvando…" : "Salvar"}
        </button>
        <button
          type="button"
          className={styles.btn}
          disabled={summarize.isPending}
          onClick={() => summarize.mutate(book.id)}
        >
          {summarize.isPending ? "Resumindo…" : "Resumir com IA"}
        </button>
      </div>
      {(update.isError || summarize.isError) && (
        <p className={styles.error}>{update.error?.message ?? summarize.error?.message}</p>
      )}
    </section>
  );
}

export default function BookPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const bookId = Number(id);
  const book = useBook(bookId);
  const progress = useProgress(bookId);
  const { data: tagCounts = [] } = useTags();
  const allTags = tagCounts.map((tc) => tc.tag);

  const [dialog, setDialog] = useState<DialogKind>(null);

  const update = useUpdateBook();
  const remove = useDeleteBook();
  const attach = useAttachTag();
  const detach = useDetachTag();

  if (book.isLoading) return <p className={styles.loading}>Loading…</p>;
  if (book.isError || !book.data) return <p className={styles.error}>Failed to load book.</p>;

  const b = book.data;

  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <img src={coverUrl(b.id)} alt="" className={styles.cover} />
        <div className={styles.headMeta}>
          <h1 className={styles.title}>{b.title}</h1>
          {b.author && <p className={styles.author}>{b.author}</p>}
          <p className={styles.meta}>
            {b.format.toUpperCase()} · {b.page_count} páginas
          </p>
          {progress.data && (
            <p className={styles.progress}>Última leitura: página {progress.data.page_no}</p>
          )}
          <div className={styles.actions}>
            <Link to={`/read/${b.id}`} className={styles.readBtn}>
              Ler
            </Link>
            <button type="button" className={styles.btn} onClick={() => setDialog("tags")}>
              Editar tags
            </button>
            <button type="button" className={styles.btn} onClick={() => setDialog("rename")}>
              Renomear
            </button>
            <button type="button" className={styles.btn} onClick={() => setDialog("delete")}>
              Excluir
            </button>
          </div>
        </div>
      </div>

      {b.tags.length > 0 && (
        <ul className={styles.tagList}>
          {b.tags.map((tag) => (
            <li key={tag.id} className={styles.tag} style={{ background: tag.color }}>
              {tag.name}
            </li>
          ))}
        </ul>
      )}

      <BookDetailsEditor key={b.id} book={b} />

      {dialog === "rename" && (
        <RenameDialog
          book={b}
          isPending={update.isPending}
          errorMessage={update.error?.message}
          onClose={() => setDialog(null)}
          onSubmit={(title) =>
            update.mutate({ id: b.id, title }, { onSuccess: () => setDialog(null) })
          }
        />
      )}

      {dialog === "tags" && (
        <TagsEditDialog
          book={b}
          allTags={allTags}
          isPending={attach.isPending || detach.isPending}
          onClose={() => setDialog(null)}
          onToggle={(tag, attached) => {
            if (attached) detach.mutate({ bookId: b.id, tagId: tag.id });
            else attach.mutate({ bookId: b.id, tagId: tag.id });
          }}
        />
      )}

      {dialog === "delete" && (
        <ConfirmDialog
          title="Delete book"
          message={`Permanently delete "${b.title}"? This cannot be undone.`}
          confirmLabel="Delete"
          danger
          isPending={remove.isPending}
          errorMessage={remove.error?.message}
          onClose={() => setDialog(null)}
          onConfirm={() => remove.mutate(b.id, { onSuccess: () => navigate("/") })}
        />
      )}
    </div>
  );
}
