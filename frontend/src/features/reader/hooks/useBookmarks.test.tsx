import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/mswServer";
import { useBookmarks, useCreateBookmark, useDeleteBookmark } from "./useBookmarks";

function makeWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

const baseBookmark = {
  id: 1,
  book_id: 5,
  page_no: 12,
  label: "Chapter 1",
  note: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("bookmark hooks", () => {
  it("list returns the bookmark array", async () => {
    server.use(
      http.get("*/api/books/5/bookmarks", () => HttpResponse.json([baseBookmark])),
    );
    const { result } = renderHook(() => useBookmarks(5), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([baseBookmark]);
  });

  it("create sends the page label payload", async () => {
    let received: unknown;
    server.use(
      http.post("*/api/books/5/bookmarks", async ({ request }) => {
        received = await request.json();
        return HttpResponse.json(baseBookmark, { status: 201 });
      }),
    );
    const { result } = renderHook(() => useCreateBookmark(5), { wrapper: makeWrapper() });
    result.current.mutate({ page_no: 12, label: "Chapter 1", note: null });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(received).toEqual({ page_no: 12, label: "Chapter 1", note: null });
  });

  it("delete hits the bookmark id endpoint", async () => {
    let hit = 0;
    server.use(
      http.delete("*/api/bookmarks/99", () => {
        hit += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { result } = renderHook(() => useDeleteBookmark(5), { wrapper: makeWrapper() });
    result.current.mutate(99);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(hit).toBe(1);
  });
});
