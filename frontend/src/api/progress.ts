import type { Schemas } from "./client";
import { ApiError, api } from "./client";

export type ProgressOut = Schemas["ProgressOut"];

export async function getProgress(bookId: number): Promise<ProgressOut | null> {
  try {
    return await api.get<ProgressOut>(`/api/books/${bookId}/progress`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

export function setProgress(bookId: number, pageNo: number) {
  return api.put<ProgressOut>(`/api/books/${bookId}/progress`, {
    body: { page_no: pageNo },
  });
}
