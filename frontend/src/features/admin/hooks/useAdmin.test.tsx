import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/mswServer";
import { useConfig, useReembedAll, useScan } from "./useAdmin";

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidate = vi.spyOn(qc, "invalidateQueries");
  function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  }
  return { Wrapper, invalidate };
}

describe("useConfig", () => {
  it("fetches /api/config and returns the data", async () => {
    const cfg = { embed_model: "BAAI/bge-small-en-v1.5", chunk_pages: 1, data_dir: "/data" };
    server.use(http.get("*/api/config", () => HttpResponse.json(cfg)));
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useConfig(), { wrapper: Wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(cfg);
  });
});

describe("useScan", () => {
  it("POSTs /api/admin/scan and returns ScanResultOut", async () => {
    const scanResult = { ingested: 3, skipped: 1, failed: 0 };
    server.use(http.post("*/api/admin/scan", () => HttpResponse.json(scanResult)));
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useScan(), { wrapper: Wrapper });

    result.current.mutate(undefined);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(scanResult);
  });
});

describe("useReembedAll", () => {
  it("POSTs /api/admin/reembed-all and invalidates books", async () => {
    const books = [{ book_id: 1, status: "reembedding" }];
    server.use(
      http.post("*/api/admin/reembed-all", () => HttpResponse.json(books, { status: 202 })),
    );
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useReembedAll(), { wrapper: Wrapper });

    result.current.mutate(undefined);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
  });
});
