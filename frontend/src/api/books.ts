import type { Schemas } from "./client";
import { api } from "./client";

export type BookOut = Schemas["BookOut"];
export type BookListOut = Schemas["BookListOut"];
export type BookCreateResponse = Schemas["BookCreateResponse"];

export interface BookFilters {
  tags?: number[];
  tag_mode?: "all" | "any";
  exclude?: number[];
  q?: string;
}

export function listBooks(filters: BookFilters = {}) {
  return api.get<BookListOut>("/api/books", { query: { ...filters } });
}

export function getBook(id: number) {
  return api.get<BookOut>(`/api/books/${id}`);
}

export function updateBook(id: number, patch: { title: string }) {
  return api.patch<BookOut>(`/api/books/${id}`, { body: { ...patch } });
}

export function deleteBook(id: number) {
  return api.delete<void>(`/api/books/${id}`);
}

export function attachBookTag(bookId: number, tagId: number) {
  return api.post<BookOut>(`/api/books/${bookId}/tags`, { body: { tag_id: tagId } });
}

export function detachBookTag(bookId: number, tagId: number) {
  return api.delete<void>(`/api/books/${bookId}/tags/${tagId}`);
}

export function reembedBook(id: number) {
  return api.post<void>(`/api/books/${id}/reembed`);
}

export function coverUrl(bookId: number): string {
  return `/api/books/${bookId}/cover`;
}
