import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getConfig, reembedAll, triggerScan, updateConfig } from "../../../api/admin";

export function useConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
    staleTime: 60_000,
  });
}

export function useScan() {
  return useMutation({ mutationFn: triggerScan });
}

export function useUpdateConfig() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: updateConfig,
    onSuccess: () => client.invalidateQueries({ queryKey: ["config"] }),
  });
}

export function useReembedAll() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: reembedAll,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["books"] });
    },
  });
}
