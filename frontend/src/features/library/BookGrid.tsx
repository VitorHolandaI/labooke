import type { BookOut } from "../../api/books";
import type { TagOut } from "../../api/tags";
import { BookCard } from "./BookCard";
import styles from "./BookGrid.module.css";

interface Props {
  books: BookOut[];
  allTags: TagOut[];
  isLoading: boolean;
  isError: boolean;
}

export function BookGrid({ books, allTags, isLoading, isError }: Props) {
  if (isLoading) return <p className={styles.status}>Loading library…</p>;
  if (isError) return <p className={styles.status}>Could not load books.</p>;
  if (books.length === 0) {
    return <p className={styles.status}>No books match your filters yet.</p>;
  }
  return (
    <div className={styles.grid}>
      {books.map((book) => (
        <BookCard key={book.id} book={book} allTags={allTags} />
      ))}
    </div>
  );
}
