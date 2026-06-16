import { useState } from "react";

import type { BookOut } from "../../api/books";
import { Modal } from "./Modal";
import styles from "./Modal.module.css";

interface Props {
  book: BookOut;
  isPending?: boolean;
  errorMessage?: string;
  onSubmit: (title: string) => void;
  onClose: () => void;
}

export function RenameDialog({ book, isPending, errorMessage, onSubmit, onClose }: Props) {
  const [draft, setDraft] = useState(book.title);

  const trimmed = draft.trim();
  const canSubmit = trimmed.length > 0 && trimmed !== book.title && !isPending;

  return (
    <Modal title="Rename book" onClose={onClose}>
      <form
        className={styles.body}
        onSubmit={(event) => {
          event.preventDefault();
          if (canSubmit) onSubmit(trimmed);
        }}
      >
        <label htmlFor="rename-title">Title</label>
        <input
          id="rename-title"
          className={styles.input}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          autoFocus
        />
        {errorMessage && <p className={styles.danger}>{errorMessage}</p>}
        <div className={styles.actions}>
          <button type="button" className={styles.btn} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={`${styles.btn} ${styles.btnPrimary}`}
            disabled={!canSubmit}
          >
            {isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
