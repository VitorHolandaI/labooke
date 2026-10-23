import { describe, expect, it } from "vitest";

import { autoTagMark, embeddingMark, summaryMark } from "./bookMarks";
import { adminBook } from "./test/adminBooks";

describe("summaryMark", () => {
  it("is done once the LLM wrote a description", () => {
    expect(summaryMark(adminBook())).toBe("done");
    expect(summaryMark(adminBook({ description: null }))).toBe("missing");
    expect(summaryMark(adminBook({ description: "" }))).toBe("missing");
  });
});

describe("embeddingMark", () => {
  it("follows the ingest status", () => {
    expect(embeddingMark(adminBook({ status: "ready" }))).toBe("done");
    expect(embeddingMark(adminBook({ status: "pending" }))).toBe("busy");
    expect(embeddingMark(adminBook({ status: "reembedding" }))).toBe("busy");
    expect(embeddingMark(adminBook({ status: "failed" }))).toBe("missing");
  });
});

describe("autoTagMark", () => {
  it("is done once the LLM classified the book, even with no tag picked", () => {
    expect(autoTagMark(adminBook({ auto_tagged_at: "2026-10-23T12:00:00Z" }))).toBe("done");
    expect(autoTagMark(adminBook())).toBe("missing");
  });

  // Hand-picked tags say nothing about whether the LLM ran.
  it("ignores manually attached tags", () => {
    const tagged = adminBook({ tags: [{ id: 1, name: "Redes", slug: "redes", color: "#000" }] });
    expect(autoTagMark(tagged)).toBe("missing");
  });
});
