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

  const recommendations = mutation.data
    ? (mutation.data.recommendations ?? mutation.data.books.map((book) => ({ book, reason: "" })))
    : [];

  return (
    <section className={styles.panel} aria-label="Ask the library">
      <div className={styles.intro}>
        <span className={styles.eyebrow}>Recomendação com IA</span>
        <h2>Que tipo de livro você procura?</h2>
        <p>Descreva um assunto, objetivo ou nível de experiência.</p>
      </div>
      <form className={styles.form} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder="Ex.: livros introdutórios sobre sistemas distribuídos"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          aria-label="Ask the library"
          autoComplete="off"
        />
        <button
          type="submit"
          className={styles.btn}
          disabled={!question.trim() || mutation.isPending}
        >
          {mutation.isPending ? "Procurando…" : "Encontrar livros"}
        </button>
      </form>
      {mutation.isPending && <p className={styles.pending}>Analisando os perfis dos livros…</p>}
      {mutation.isError && (
        <p className={styles.error}>Não foi possível consultar a biblioteca agora.</p>
      )}
      {mutation.data && (
        <div className={styles.answer}>
          <p className={styles.text}>{mutation.data.answer}</p>
          {recommendations.length > 0 ? (
            <div className={styles.books}>
              {recommendations.map(({ book, reason }, index) => (
                <Link className={styles.book} to={`/book/${book.id}`} key={book.id}>
                  <span className={styles.rank}>{String(index + 1).padStart(2, "0")}</span>
                  <span className={styles.bookCopy}>
                    <strong>{book.title}</strong>
                    {book.author && <small>{book.author}</small>}
                    {reason && <span>{reason}</span>}
                  </span>
                  <span className={styles.arrow} aria-hidden="true">
                    →
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>Tente descrever o assunto com outros termos.</p>
          )}
        </div>
      )}
    </section>
  );
}
