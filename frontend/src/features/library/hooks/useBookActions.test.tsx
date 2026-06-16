import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/mswServer";
import {
  useAttachTag,
  useDeleteBook,
  useDetachTag,
  useReembedBook,
  useUpdateBook,
} from "./useBookActions";

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

function stubBook() {
  return {
    id: 1,
    sha256: "aa",
    title: "T",
    author: null,
    format: "pdf",
    page_count: 1,
    status: "ready",
    ingest_error: null,
    tags: [],
  };
}

describe("useUpdateBook", () => {
  it("PATCHes /api/books/:id and invalidates books, book, tags", async () => {
    server.use(http.patch("*/api/books/:id", () => HttpResponse.json(stubBook())));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useUpdateBook(), { wrapper: Wrapper });

    result.current.mutate({ id: 1, title: "New Title" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useDeleteBook", () => {
  it("DELETEs /api/books/:id and invalidates queries", async () => {
    server.use(http.delete("*/api/books/:id", () => new HttpResponse(null, { status: 204 })));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useDeleteBook(), { wrapper: Wrapper });

    result.current.mutate(1);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useReembedBook", () => {
  it("POSTs /api/books/:id/reembed and invalidates queries", async () => {
    server.use(
      http.post("*/api/books/:id/reembed", () => new HttpResponse(null, { status: 202 })),
    );
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useReembedBook(), { wrapper: Wrapper });

    result.current.mutate(1);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useAttachTag", () => {
  it("POSTs /api/books/:bookId/tags and invalidates queries", async () => {
    server.use(http.post("*/api/books/:bookId/tags", () => HttpResponse.json(stubBook())));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useAttachTag(), { wrapper: Wrapper });

    result.current.mutate({ bookId: 1, tagId: 3 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useDetachTag", () => {
  it("DELETEs /api/books/:bookId/tags/:tagId and invalidates queries", async () => {
    server.use(
      http.delete(
        "*/api/books/:bookId/tags/:tagId",
        () => new HttpResponse(null, { status: 204 }),
      ),
    );
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useDetachTag(), { wrapper: Wrapper });

    result.current.mutate({ bookId: 1, tagId: 3 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});
