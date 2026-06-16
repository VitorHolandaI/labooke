import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import { server } from "../../../test/mswServer";
import { useUpload } from "./useUpload";

function wrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

describe("useUpload", () => {
  it("sends multipart payload with file field and tag_ids", async () => {
    let receivedTagIds: string[] = [];
    let receivedFilePresent = false;
    server.use(
      http.post("*/api/books", async ({ request }) => {
        const form = await request.formData();
        receivedTagIds = form.getAll("tag_ids").map(String);
        receivedFilePresent = form.has("file");
        return HttpResponse.json({ id: 1, status: "pending" }, { status: 202 });
      }),
    );

    const { result } = renderHook(() => useUpload(), { wrapper: wrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        file: new File(["hello"], "sample.txt", { type: "text/plain" }),
        tagIds: [4, 9],
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(receivedFilePresent).toBe(true);
    expect(receivedTagIds).toEqual(["4", "9"]);
  });
});
