import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/mswServer";
import { useProgress, useSetProgress } from "./useProgress";

function makeWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useProgress", () => {
  it("returns null on 404", async () => {
    server.use(
      http.get("*/api/books/1/progress", () =>
        HttpResponse.json(
          { code: "progress_not_found", message: "none" },
          { status: 404 },
        ),
      ),
    );
    const { result } = renderHook(() => useProgress(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });

  it("returns progress when set", async () => {
    server.use(
      http.get("*/api/books/2/progress", () =>
        HttpResponse.json({ book_id: 2, page_no: 17, updated_at: "x" }),
      ),
    );
    const { result } = renderHook(() => useProgress(2), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.page_no).toBe(17);
  });

  it("PUT sends payload and caches result", async () => {
    let received: { page_no: number } | undefined;
    server.use(
      http.put("*/api/books/3/progress", async ({ request }) => {
        received = (await request.json()) as { page_no: number };
        return HttpResponse.json({ book_id: 3, page_no: received.page_no, updated_at: "y" });
      }),
    );
    const { result } = renderHook(() => useSetProgress(3), { wrapper: makeWrapper() });
    result.current.mutate(42);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(received).toEqual({ page_no: 42 });
  });
});
