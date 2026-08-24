import { Link } from "react-router-dom";

import { coverUrl } from "../../api/books";
import { useRecentBooks } from "./hooks/useRecentBooks";
import styles from "./RecentBooks.module.css";

export function RecentBooks() {
  const { data, isLoading } = useRecentBooks();
  const books = data?.items ?? [];

  if (isLoading || books.length === 0) return null;

  return (
    <section className={styles.section} aria-label="Continue reading">
      <h2 className={styles.heading}>Continue lendo</h2>
      <div className={styles.row}>
        {books.map((book) => (
          <Link key={book.id} to={`/read/${book.id}`} className={styles.card}>
            <img
              src={coverUrl(book.id)}
              alt=""
              loading="lazy"
              className={styles.cover}
            />
            <span className={styles.title}>{book.title}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
