import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { BookmarkCreateInput, BookmarkOut } from "../../../api/bookmarks";
import {
  createBookmark,
  deleteBookmark,
  listBookmarks,
  updateBookmarkNote,
} from "../../../api/bookmarks";

const bookmarksKey = (bookId: number) => ["bookmarks", bookId] as const;

export function useBookmarks(bookId: number) {
  return useQuery<BookmarkOut[]>({
    queryKey: bookmarksKey(bookId),
    queryFn: () => listBookmarks(bookId),
    enabled: bookId > 0,
  });
}

export function useCreateBookmark(bookId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: BookmarkCreateInput) => createBookmark(bookId, body),
    onSuccess: () => client.invalidateQueries({ queryKey: bookmarksKey(bookId) }),
  });
}

export function useUpdateBookmarkNote(bookId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: number; note: string | null }) =>
      updateBookmarkNote(id, note),
    onSuccess: () => client.invalidateQueries({ queryKey: bookmarksKey(bookId) }),
  });
}

export function useDeleteBookmark(bookId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteBookmark(id),
    onSuccess: () => client.invalidateQueries({ queryKey: bookmarksKey(bookId) }),
  });
}
