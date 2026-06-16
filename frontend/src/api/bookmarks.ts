import type { Schemas } from "./client";
import { api } from "./client";

export type BookmarkOut = Schemas["BookmarkOut"];

export interface BookmarkCreateInput {
  page_no: number;
  label: string;
  note?: string | null;
}

export function listBookmarks(bookId: number) {
  return api.get<BookmarkOut[]>(`/api/books/${bookId}/bookmarks`);
}

export function createBookmark(bookId: number, body: BookmarkCreateInput) {
  return api.post<BookmarkOut>(`/api/books/${bookId}/bookmarks`, { body: { ...body } });
}

export function updateBookmarkNote(bookmarkId: number, note: string | null) {
  return api.patch<BookmarkOut>(`/api/bookmarks/${bookmarkId}`, { body: { note } });
}

export function deleteBookmark(bookmarkId: number) {
  return api.delete<void>(`/api/bookmarks/${bookmarkId}`);
}
