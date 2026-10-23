import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { BookOut } from "../../../api/books";
import { server } from "../../../test/mswServer";
import { booksPollingInterval, useBooks } from "./useBooks";

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

function listWith(...statuses: string[]) {
  return { items: statuses.map((status, index) => ({ id: index, status }) as BookOut) };
}

describe("booksPollingInterval", () => {
  it("polls while a book is still being ingested", () => {
    expect(booksPollingInterval(listWith("ready", "pending"))).toBeGreaterThan(0);
  });

  // Regression: re-embedded books kept their spinner until a manual reload.
  it("polls while a book is being re-embedded", () => {
    expect(booksPollingInterval(listWith("reembedding"))).toBeGreaterThan(0);
  });

  it("stops once every book has settled", () => {
    expect(booksPollingInterval(listWith("ready", "failed"))).toBe(false);
    expect(booksPollingInterval(undefined)).toBe(false);
  });
});
