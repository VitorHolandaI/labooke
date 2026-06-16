import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "../test/mswServer";
import { ApiError, api } from "./client";

describe("api client", () => {
  it("decodes a JSON GET response", async () => {
    server.use(
      http.get("http://localhost/api/tags", () =>
        HttpResponse.json([{ id: 1, name: "fiction", slug: "fiction", color: "#aaa" }]),
      ),
    );
    const tags = await api.get<Array<{ name: string }>>("http://localhost/api/tags");
    expect(tags[0]?.name).toBe("fiction");
  });

  it("appends array query params", async () => {
    let receivedUrl: string | undefined;
    server.use(
      http.get("http://localhost/api/books", ({ request }) => {
        receivedUrl = request.url;
        return HttpResponse.json([]);
      }),
    );
    await api.get("http://localhost/api/books", {
      query: { tags: ["1", "2"], tag_mode: "all" },
    });
    const url = new URL(receivedUrl!);
    expect(url.searchParams.getAll("tags")).toEqual(["1", "2"]);
    expect(url.searchParams.get("tag_mode")).toBe("all");
  });

  it("throws ApiError on non-2xx with code and message", async () => {
    server.use(
      http.get("http://localhost/api/books/99", () =>
        HttpResponse.json({ code: "book_not_found", message: "no such book" }, { status: 404 }),
      ),
    );
    await expect(api.get("http://localhost/api/books/99")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      code: "book_not_found",
      message: "no such book",
    });
  });

  it("sends JSON body on POST", async () => {
    let receivedBody: unknown;
    server.use(
      http.post("http://localhost/api/tags", async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ id: 9, name: "new", slug: "new", color: "#fff" });
      }),
    );
    await api.post("http://localhost/api/tags", { body: { name: "new", color: "#fff" } });
    expect(receivedBody).toEqual({ name: "new", color: "#fff" });
  });

  it("returns undefined for 204 responses", async () => {
    server.use(
      http.delete("http://localhost/api/tags/1", () => new HttpResponse(null, { status: 204 })),
    );
    const result = await api.delete("http://localhost/api/tags/1");
    expect(result).toBeUndefined();
  });

  it("ApiError preserves details payload", () => {
    const err = new ApiError(400, "bad", "validation", { detail: [{ msg: "x" }] });
    expect(err.status).toBe(400);
    expect(err.details).toEqual({ detail: [{ msg: "x" }] });
  });
});
