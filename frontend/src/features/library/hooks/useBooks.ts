import { useQuery } from "@tanstack/react-query";

import type { BookFilters, BookListOut } from "../../../api/books";
import { listBooks } from "../../../api/books";

export function booksQueryKey(filters: BookFilters) {
  return ["books", filters] as const;
}

function pollingInterval(data: BookListOut | undefined): number | false {
  if (!data) return false;
  return data.items.some((book) => book.status === "pending") ? 2000 : false;
}

export function useBooks(filters: BookFilters) {
  return useQuery({
    queryKey: booksQueryKey(filters),
    queryFn: () => listBooks(filters),
    refetchInterval: ({ state }) => pollingInterval(state.data),
  });
}
