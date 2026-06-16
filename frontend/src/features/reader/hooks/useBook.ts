import { useQuery } from "@tanstack/react-query";

import type { BookOut } from "../../../api/books";
import { getBook } from "../../../api/books";

export function useBook(id: number) {
  return useQuery<BookOut>({
    queryKey: ["book", id],
    queryFn: () => getBook(id),
    enabled: Number.isFinite(id) && id > 0,
  });
}
