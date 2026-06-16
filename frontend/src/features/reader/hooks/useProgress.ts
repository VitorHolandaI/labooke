import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import type { ProgressOut } from "../../../api/progress";
import { getProgress, setProgress } from "../../../api/progress";

export function useProgress(bookId: number) {
  return useQuery<ProgressOut | null>({
    queryKey: ["progress", bookId],
    queryFn: () => getProgress(bookId),
    enabled: bookId > 0,
  });
}

export function useSetProgress(bookId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (pageNo: number) => setProgress(bookId, pageNo),
    onSuccess: (data) => client.setQueryData(["progress", bookId], data),
  });
}

export function useDebouncedProgress(
  bookId: number,
  page: number,
  delay = 800,
): void {
  const mut = useSetProgress(bookId);
  // keep a stable ref to mutate so it's never in the effect dep array
  const mutRef = useRef(mut.mutate);
  useEffect(() => { mutRef.current = mut.mutate; });

  const initial = useRef(page);
  // reset baseline when bookId changes so the old book's last page is never
  // saved to the new book during the brief window before the viewer remounts
  useEffect(() => {
    initial.current = page;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  useEffect(() => {
    if (page === initial.current) return;
    const handle = window.setTimeout(() => mutRef.current(page), delay);
    return () => window.clearTimeout(handle);
  }, [bookId, page, delay]);
}
