import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { askQuestion } from "../../api/ask";
import styles from "./AskPanel.module.css";

export function AskPanel() {
  const [question, setQuestion] = useState("");
  const mutation = useMutation({ mutationFn: (q: string) => askQuestion(q) });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || mutation.isPending) return;
    mutation.mutate(q);
  }

  return (
    <section className={styles.panel} aria-label="Ask the library">
      <form className={styles.form} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder="Pergunte: 'um livro sobre ciência'…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          aria-label="Ask the library"
        />
        <button
          type="submit"
          className={styles.btn}
          disabled={!question.trim() || mutation.isPending}
        >
          {mutation.isPending ? "Perguntando…" : "Perguntar"}
        </button>
      </form>
      {mutation.isError && (
        <p className={styles.error}>{mutation.error?.message}</p>
      )}
      {mutation.data && (
        <div className={styles.answer}>
          <p className={styles.text}>{mutation.data.answer}</p>
          {mutation.data.books.length > 0 && (
            <ul className={styles.books}>
              {mutation.data.books.map((book) => (
                <li key={book.id}>
                  <Link to={`/book/${book.id}`}>{book.title}</Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
