import { useQuery } from "@tanstack/react-query";

import { listTags } from "../../../api/tags";

export const tagsQueryKey = ["tags"] as const;

export function useTags() {
  return useQuery({
    queryKey: tagsQueryKey,
    queryFn: () => listTags(),
  });
}
