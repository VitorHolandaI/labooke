import { useQuery } from "@tanstack/react-query";

import { listBooks } from "../../../api/books";

export function useRecentBooks() {
  return useQuery({
    queryKey: ["books", "recent"],
    queryFn: () => listBooks({ sort: "recent" }),
  });
}
