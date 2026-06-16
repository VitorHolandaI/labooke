import type { Schemas } from "./client";
import { api } from "./client";

export type PageTextOut = Schemas["PageTextOut"];

export function getPageText(bookId: number, pageNo: number) {
  return api.get<PageTextOut>(`/api/books/${bookId}/pages/${pageNo}`);
}

export function bookFileUrl(bookId: number): string {
  return `/api/books/${bookId}/file`;
}
