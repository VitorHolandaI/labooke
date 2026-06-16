import { useState } from "react";

import type { BookmarkOut } from "../../api/bookmarks";
import {
  useBookmarks,
  useCreateBookmark,
  useDeleteBookmark,
  useUpdateBookmarkNote,
} from "./hooks/useBookmarks";
import styles from "./BookmarkDrawer.module.css";

interface Props {
  bookId: number;
  currentPage: number;
  onJump: (page: number) => void;
}

export function BookmarkDrawer({ bookId, currentPage, onJump }: Props) {
  const bookmarks = useBookmarks(bookId);
  const create = useCreateBookmark(bookId);
  const update = useUpdateBookmarkNote(bookId);
  const remove = useDeleteBookmark(bookId);
  const [open, setOpen] = useState(true);
  const [draftLabel, setDraftLabel] = useState("");

  const onCurrent = bookmarks.data?.find((bm) => bm.page_no === currentPage);

  const handleAdd = () => {
    const label = draftLabel.trim() || `Page ${currentPage}`;
    create.mutate({ page_no: currentPage, label, note: null });
    setDraftLabel("");
  };

  return (
    <aside className={open ? styles.open : styles.closed}>
      <header className={styles.header}>
        <h2 className={styles.heading}>Bookmarks</h2>
        <button
          type="button"
          className={styles.toggle}
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close bookmarks" : "Open bookmarks"}
        >
          {open ? "✕" : "☆"}
        </button>
      </header>
      {open && (
        <>
          <div className={styles.add}>
            <input
              className={styles.labelInput}
              placeholder={`Label (default: Page ${currentPage})`}
              value={draftLabel}
              onChange={(event) => setDraftLabel(event.target.value)}
            />
            <button
              type="button"
              className={styles.addButton}
              onClick={handleAdd}
              disabled={Boolean(onCurrent)}
            >
              {onCurrent ? "Already bookmarked" : `+ Bookmark page ${currentPage}`}
            </button>
          </div>
          {bookmarks.isLoading && <p className={styles.muted}>Loading…</p>}
          {bookmarks.isError && <p className={styles.error}>Failed to load.</p>}
          <ul className={styles.list}>
            {(bookmarks.data ?? []).map((bm) => (
              <BookmarkRow
                key={bm.id}
                bookmark={bm}
                isCurrent={bm.page_no === currentPage}
                onJump={() => onJump(bm.page_no)}
                onSaveNote={(note) => update.mutate({ id: bm.id, note })}
                onDelete={() => remove.mutate(bm.id)}
              />
            ))}
            {bookmarks.data?.length === 0 && (
              <li className={styles.empty}>No bookmarks yet.</li>
            )}
          </ul>
        </>
      )}
    </aside>
  );
}

interface RowProps {
  bookmark: BookmarkOut;
  isCurrent: boolean;
  onJump: () => void;
  onSaveNote: (note: string | null) => void;
  onDelete: () => void;
}

function BookmarkRow({ bookmark, isCurrent, onJump, onSaveNote, onDelete }: RowProps) {
  const [note, setNote] = useState(bookmark.note ?? "");
  const dirty = (bookmark.note ?? "") !== note;

  return (
    <li className={isCurrent ? styles.entryCurrent : styles.entry}>
      <div className={styles.entryHead}>
        <button type="button" className={styles.jump} onClick={onJump}>
          <span className={styles.label}>{bookmark.label}</span>
          <span className={styles.page}>p. {bookmark.page_no}</span>
        </button>
        <button
          type="button"
          className={styles.delete}
          aria-label="Delete bookmark"
          onClick={onDelete}
        >
          ×
        </button>
      </div>
      <textarea
        className={styles.note}
        placeholder="Add a note…"
        value={note}
        onChange={(event) => setNote(event.target.value)}
        rows={2}
      />
      {dirty && (
        <div className={styles.noteActions}>
          <button type="button" onClick={() => onSaveNote(note || null)}>
            Save
          </button>
          <button type="button" onClick={() => setNote(bookmark.note ?? "")}>
            Reset
          </button>
        </div>
      )}
    </li>
  );
}
