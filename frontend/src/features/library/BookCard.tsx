import { useState } from "react";
import { Link } from "react-router-dom";

import type { BookOut } from "../../api/books";
import { coverUrl } from "../../api/books";
import type { TagOut } from "../../api/tags";
import { BookActionsMenu } from "./BookActionsMenu";
import { ConfirmDialog } from "./ConfirmDialog";
import { RenameDialog } from "./RenameDialog";
import { TagsEditDialog } from "./TagsEditDialog";
import {
  useAttachTag,
  useDeleteBook,
  useDetachTag,
  useReembedBook,
  useUpdateBook,
} from "./hooks/useBookActions";
import styles from "./BookCard.module.css";

interface Props {
  book: BookOut;
  allTags: TagOut[];
}

type DialogKind = null | "rename" | "tags" | "reembed" | "delete";

const STATUS_LABELS: Record<string, string> = {
  pending: "Ingesting…",
  reembedding: "Re-embedding…",
  failed: "Failed",
  ready: "",
};

export function BookCard({ book, allTags }: Props) {
  const statusLabel = STATUS_LABELS[book.status] ?? book.status;
  const isReady = book.status === "ready";
  const [dialog, setDialog] = useState<DialogKind>(null);

  const update = useUpdateBook();
  const remove = useDeleteBook();
  const reembed = useReembedBook();
  const attach = useAttachTag();
  const detach = useDetachTag();

  const close = () => setDialog(null);

  const cover = (
    <img
      src={coverUrl(book.id)}
      alt=""
      loading="lazy"
      className={styles.cover}
      onError={(event) => {
        (event.currentTarget as HTMLImageElement).style.visibility = "hidden";
      }}
    />
  );

  return (
    <article className={styles.card} aria-busy={!isReady}>
      <div className={styles.coverWrap}>
        {isReady ? <Link to={`/book/${book.id}`}>{cover}</Link> : cover}
        {statusLabel && (
          <span className={book.status === "failed" ? styles.badgeError : styles.badge}>
            {statusLabel}
          </span>
        )}
        {(book.status === "pending" || book.status === "reembedding") && (
          <div className={styles.progressBar} aria-hidden="true" />
        )}
        <BookActionsMenu
          onRename={() => setDialog("rename")}
          onEditTags={() => setDialog("tags")}
          onReembed={() => setDialog("reembed")}
          onDelete={() => setDialog("delete")}
        />
      </div>
      <div className={styles.meta}>
        <h3 className={styles.title} title={book.title}>
          {isReady ? <Link to={`/book/${book.id}`}>{book.title}</Link> : book.title}
        </h3>
        {book.author && <p className={styles.author}>{book.author}</p>}
        {book.tags.length > 0 && (
          <ul className={styles.tags}>
            {book.tags.map((tag) => (
              <li key={tag.id} className={styles.tag} style={{ background: tag.color }}>
                {tag.name}
              </li>
            ))}
          </ul>
        )}
        {book.status === "failed" && book.ingest_error && (
          <p className={styles.error}>{book.ingest_error}</p>
        )}
      </div>

      {dialog === "rename" && (
        <RenameDialog
          book={book}
          isPending={update.isPending}
          errorMessage={update.error?.message}
          onClose={close}
          onSubmit={(title) =>
            update.mutate({ id: book.id, title }, { onSuccess: close })
          }
        />
      )}

      {dialog === "tags" && (
        <TagsEditDialog
          book={book}
          allTags={allTags}
          isPending={attach.isPending || detach.isPending}
          onClose={close}
          onToggle={(tag, attached) => {
            if (attached) detach.mutate({ bookId: book.id, tagId: tag.id });
            else attach.mutate({ bookId: book.id, tagId: tag.id });
          }}
        />
      )}

      {dialog === "reembed" && (
        <ConfirmDialog
          title="Re-embed book"
          message={`Rebuild embeddings for "${book.title}"? This may take a moment.`}
          confirmLabel="Re-embed"
          isPending={reembed.isPending}
          errorMessage={reembed.error?.message}
          onClose={close}
          onConfirm={() => reembed.mutate(book.id, { onSuccess: close })}
        />
      )}

      {dialog === "delete" && (
        <ConfirmDialog
          title="Delete book"
          message={`Permanently delete "${book.title}"? This cannot be undone.`}
          confirmLabel="Delete"
          danger
          isPending={remove.isPending}
          errorMessage={remove.error?.message}
          onClose={close}
          onConfirm={() => remove.mutate(book.id, { onSuccess: close })}
        />
      )}
    </article>
  );
}
