import { useQuery } from "@tanstack/react-query";

import type { SearchInput } from "../../../api/search";
import { searchLibrary } from "../../../api/search";

export function searchQueryKey(input: SearchInput) {
  return ["search", input] as const;
}

export function useSearch(input: SearchInput | null) {
  return useQuery({
    queryKey: input ? searchQueryKey(input) : ["search", null],
    queryFn: () => (input ? searchLibrary(input) : Promise.reject(new Error("disabled"))),
    enabled: Boolean(input && input.q.trim()),
  });
}
