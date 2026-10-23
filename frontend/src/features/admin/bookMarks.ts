import type { BookOut } from "../../api/books";

export type ChecklistMark = "done" | "missing" | "busy";

/**
 * Whether the LLM already wrote this book's summary.
 *
 * Example: `summaryMark(book) === "missing"` picks books to summarize.
 */
export function summaryMark(book: BookOut): ChecklistMark {
  return book.description ? "done" : "missing";
}

/**
 * Whether the book's content vectors exist; failed rebuilds delete the old
 * rows first, so a failed book has none worth keeping.
 *
 * Example: `embeddingMark(book) === "busy"` while it re-embeds.
 */
export function embeddingMark(book: BookOut): ChecklistMark {
  if (book.status === "ready") return "done";
  if (book.status === "failed") return "missing";
  return "busy";
}

/**
 * Whether the LLM has classified the book against the tag list.
 *
 * Example: `autoTagMark(book) === "done"` even when no tag fitted.
 */
export function autoTagMark(book: BookOut): ChecklistMark {
  return book.auto_tagged_at ? "done" : "missing";
}
