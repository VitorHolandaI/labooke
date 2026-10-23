import { useQuery } from "@tanstack/react-query";

import type { BookFilters, BookListOut } from "../../../api/books";
import { listBooks } from "../../../api/books";

export function booksQueryKey(filters: BookFilters) {
  return ["books", filters] as const;
}

const BUSY_STATUSES = new Set(["pending", "reembedding"]);

/**
 * Poll every 2s while any book is still being embedded, so badges settle.
 *
 * Example: `refetchInterval: ({ state }) => booksPollingInterval(state.data)`.
 */
export function booksPollingInterval(data: BookListOut | undefined): number | false {
  if (!data) return false;
  return data.items.some((book) => BUSY_STATUSES.has(book.status)) ? 2000 : false;
}

export function useBooks(filters: BookFilters) {
  return useQuery({
    queryKey: booksQueryKey(filters),
    queryFn: () => listBooks(filters),
    refetchInterval: ({ state }) => booksPollingInterval(state.data),
  });
}
