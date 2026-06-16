import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/mswServer";
import { useTags } from "./useTags";

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useTags", () => {
  it("fetches the tag list with counts", async () => {
    server.use(
      http.get("*/api/tags", () =>
        HttpResponse.json([
          { tag: { id: 1, name: "fiction", slug: "fiction", color: "#aaa" }, count: 3 },
          { tag: { id: 2, name: "tech", slug: "tech", color: "#bbb" }, count: 7 },
        ]),
      ),
    );
    const { result } = renderHook(() => useTags(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].tag.name).toBe("fiction");
    expect(result.current.data?.[1].count).toBe(7);
  });
});
