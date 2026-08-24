import type { BookOut } from "./books";
import { api } from "./client";

export interface AskResponse {
  answer: string;
  books: BookOut[];
}

export function summarizeBook(bookId: number) {
  return api.post<BookOut>(`/api/books/${bookId}/summarize`);
}

export function askQuestion(question: string) {
  return api.post<AskResponse>("/api/ask", { body: { question } });
}
