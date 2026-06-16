import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createTag, deleteTag, mergeTags, updateTag } from "../../../api/tags";
import type { Schemas } from "../../../api/client";

function useInvalidateTags() {
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: ["tags"] });
}

function useInvalidateAll() {
  const client = useQueryClient();
  return () => {
    client.invalidateQueries({ queryKey: ["tags"] });
    client.invalidateQueries({ queryKey: ["books"] });
    client.invalidateQueries({ queryKey: ["book"] });
  };
}

export function useCreateTag() {
  const invalidate = useInvalidateTags();
  return useMutation({
    mutationFn: (body: Schemas["TagCreate"]) => createTag(body),
    onSuccess: invalidate,
  });
}

export function useUpdateTag() {
  const invalidate = useInvalidateTags();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number } & Schemas["TagUpdate"]) =>
      updateTag(id, body),
    onSuccess: invalidate,
  });
}

export function useDeleteTag() {
  const invalidate = useInvalidateTags();
  return useMutation({
    mutationFn: (id: number) => deleteTag(id),
    onSuccess: invalidate,
  });
}

export function useMergeTags() {
  const invalidate = useInvalidateAll();
  return useMutation({
    mutationFn: ({ sourceId, targetId }: { sourceId: number; targetId: number }) =>
      mergeTags({ source_id: sourceId, target_id: targetId }),
    onSuccess: invalidate,
  });
}
