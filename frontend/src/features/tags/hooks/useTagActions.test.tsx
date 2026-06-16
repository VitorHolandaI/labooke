import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { server } from "../../../test/mswServer";
import {
  useCreateTag,
  useDeleteTag,
  useMergeTags,
  useUpdateTag,
} from "./useTagActions";

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

function stubTag() {
  return { id: 1, name: "fiction", slug: "fiction", color: "#f00" };
}

describe("useCreateTag", () => {
  it("POSTs /api/tags and invalidates tags", async () => {
    server.use(http.post("*/api/tags", () => HttpResponse.json(stubTag(), { status: 201 })));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useCreateTag(), { wrapper: Wrapper });

    result.current.mutate({ name: "fiction", slug: "fiction", color: "#f00" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useUpdateTag", () => {
  it("PATCHes /api/tags/:id and invalidates tags", async () => {
    server.use(http.patch("*/api/tags/:id", () => HttpResponse.json(stubTag())));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useUpdateTag(), { wrapper: Wrapper });

    result.current.mutate({ id: 1, name: "sci-fi" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useDeleteTag", () => {
  it("DELETEs /api/tags/:id and invalidates tags", async () => {
    server.use(http.delete("*/api/tags/:id", () => new HttpResponse(null, { status: 204 })));
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useDeleteTag(), { wrapper: Wrapper });

    result.current.mutate(1);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
  });
});

describe("useMergeTags", () => {
  it("POSTs /api/tags/merge and invalidates tags, books, book", async () => {
    server.use(
      http.post("*/api/tags/merge", () => new HttpResponse(null, { status: 204 })),
    );
    const { Wrapper, invalidate } = makeWrapper();
    const { result } = renderHook(() => useMergeTags(), { wrapper: Wrapper });

    result.current.mutate({ sourceId: 1, targetId: 2 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["tags"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["books"] }));
    expect(invalidate).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ["book"] }));
  });
});
