import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  attachBookTag,
  deleteBook,
  detachBookTag,
  reembedBook,
  updateBook,
  type BookUpdate,
} from "../../../api/books";

function useInvalidate() {
  const client = useQueryClient();
  return () => {
    client.invalidateQueries({ queryKey: ["books"] });
    client.invalidateQueries({ queryKey: ["book"] });
    client.invalidateQueries({ queryKey: ["tags"] });
  };
}

export function useUpdateBook() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, ...patch }: { id: number } & BookUpdate) => updateBook(id, patch),
    onSuccess: invalidate,
  });
}

export function useDeleteBook() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: number) => deleteBook(id),
    onSuccess: invalidate,
  });
}

export function useReembedBook() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: number) => reembedBook(id),
    onSuccess: invalidate,
  });
}

export function useAttachTag() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ bookId, tagId }: { bookId: number; tagId: number }) =>
      attachBookTag(bookId, tagId),
    onSuccess: invalidate,
  });
}

export function useDetachTag() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ bookId, tagId }: { bookId: number; tagId: number }) =>
      detachBookTag(bookId, tagId),
    onSuccess: invalidate,
  });
}
