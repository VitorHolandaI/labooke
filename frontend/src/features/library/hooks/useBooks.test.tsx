import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/mswServer";
import { useBooks } from "./useBooks";

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useBooks", () => {
  it("forwards tag and exclude filters as query params", async () => {
    let receivedUrl: string | undefined;
    server.use(
      http.get("*/api/books", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json({ items: [] });
      }),
    );

    const { result } = renderHook(
      () => useBooks({ tags: [1, 2], exclude: [3], tag_mode: "all" }),
      { wrapper: wrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const url = new URL(receivedUrl!);
    expect(url.searchParams.getAll("tags")).toEqual(["1", "2"]);
    expect(url.searchParams.getAll("exclude")).toEqual(["3"]);
    expect(url.searchParams.get("tag_mode")).toBe("all");
  });
});
