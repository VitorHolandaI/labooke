import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

export const BOOKS_REFRESH_MS = 5000;

/**
 * Refetch the book list while server-side LLM work is running, since those
 * jobs don't change a status the list could poll on by itself.
 *
 * Example: `useBooksRefresh(waitingForSummaries);`
 */
export function useBooksRefresh(active: boolean): void {
  const queryClient = useQueryClient();
  useEffect(() => {
    if (!active) return;
    const handle = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    }, BOOKS_REFRESH_MS);
    return () => window.clearInterval(handle);
  }, [active, queryClient]);
}
