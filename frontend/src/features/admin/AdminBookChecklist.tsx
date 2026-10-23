import type { ReactNode } from "react";

import type { BookOut } from "../../api/books";
import type { ChecklistMark } from "./bookMarks";
import type { BookSelection } from "./hooks/useBookSelection";
import styles from "./AdminPage.module.css";

const MARK_SYMBOL: Record<ChecklistMark, string> = { done: "✓", missing: "✗", busy: "⟳" };
const MARK_LABEL: Record<ChecklistMark, string> = {
  done: "Feito",
  missing: "Pendente",
  busy: "Em andamento",
};
const MARK_CLASS: Record<ChecklistMark, string> = {
  done: styles.markDone,
  missing: styles.markMissing,
  busy: styles.markBusy,
};

interface Props {
  books: readonly BookOut[];
  selection: BookSelection;
  markOf: (book: BookOut) => ChecklistMark;
  /** Label for the button that marks every book still missing this step. */
  selectMissingLabel: string;
  detailOf?: (book: BookOut) => string | null;
  /** The panel's own action buttons, shown after the selection buttons. */
  children?: ReactNode;
}

/**
 * Book list with checkboxes and a done/missing mark for one admin step.
 *
 * Example: `<AdminBookChecklist books={b} selection={s} markOf={summaryMark} … />`
 */
export function AdminBookChecklist({
  books,
  selection,
  markOf,
  selectMissingLabel,
  detailOf,
  children,
}: Props) {
  const missingIds = books.filter((book) => markOf(book) === "missing").map((book) => book.id);
  return (
    <>
      <div className={styles.row}>
        <button
          type="button"
          className={styles.btn}
          onClick={() => selection.selectIds(books.map((book) => book.id))}
        >
          Marcar todos
        </button>
        <button
          type="button"
          className={styles.btn}
          onClick={() => selection.selectIds(missingIds)}
          disabled={missingIds.length === 0}
        >
          {selectMissingLabel}
        </button>
        <button type="button" className={styles.btn} onClick={selection.clear}>
          Desmarcar todos
        </button>
        {children}
      </div>
      <ul className={styles.bookList}>
        {books.map((book) => (
          <ChecklistRow
            key={book.id}
            book={book}
            mark={markOf(book)}
            detail={detailOf?.(book) ?? null}
            checked={selection.selected.has(book.id)}
            onToggle={() => selection.toggle(book.id)}
          />
        ))}
      </ul>
    </>
  );
}

interface RowProps {
  book: BookOut;
  mark: ChecklistMark;
  detail: string | null;
  checked: boolean;
  onToggle: () => void;
}

function ChecklistRow({ book, mark, detail, checked, onToggle }: RowProps) {
  return (
    <li className={styles.bookRow}>
      <label className={styles.bookLabel}>
        <input type="checkbox" checked={checked} onChange={onToggle} />
        <span className={MARK_CLASS[mark]} aria-label={MARK_LABEL[mark]} title={MARK_LABEL[mark]}>
          {MARK_SYMBOL[mark]}
        </span>
        <span className={styles.bookTitle}>{book.title}</span>
        {detail && <span className={styles.bookTags}>{detail}</span>}
      </label>
    </li>
  );
}
