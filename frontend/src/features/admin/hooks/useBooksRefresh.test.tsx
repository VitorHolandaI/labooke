import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BOOKS_REFRESH_MS, useBooksRefresh } from "./useBooksRefresh";

function wrapperFor(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useBooksRefresh", () => {
  it("refetches the book list on an interval while active", () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    renderHook(() => useBooksRefresh(true), { wrapper: wrapperFor(client) });

    vi.advanceTimersByTime(BOOKS_REFRESH_MS * 2);

    expect(invalidate).toHaveBeenCalledTimes(2);
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["books"] });
  });

  it("stays quiet while inactive", () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    renderHook(() => useBooksRefresh(false), { wrapper: wrapperFor(client) });

    vi.advanceTimersByTime(BOOKS_REFRESH_MS * 3);

    expect(invalidate).not.toHaveBeenCalled();
  });
});
