import { describe, expect, it, vi } from "vitest";

const { getDocumentMock } = vi.hoisted(() => ({
  getDocumentMock: vi.fn(() => ({
    promise: Promise.resolve({ numPages: 1 }),
    destroy: vi.fn(() => Promise.resolve()),
  })),
}));

vi.mock("pdfjs-dist", () => ({ GlobalWorkerOptions: {}, getDocument: getDocumentMock }));
vi.mock("pdfjs-dist/build/pdf.worker.min.mjs?url", () => ({ default: "/pdf.worker.mjs" }));

import { openPdfDocument, PDFJS_WASM_URL } from "./pdfDocument";

describe("openPdfDocument", () => {
  it("passes the wasm decoder directory pdf.js 6 needs for scanned pages", () => {
    openPdfDocument({ url: "/api/books/194/file" });

    expect(getDocumentMock).toHaveBeenCalledWith({
      url: "/api/books/194/file",
      wasmUrl: PDFJS_WASM_URL,
    });
    expect(PDFJS_WASM_URL.endsWith("pdfjs-wasm/")).toBe(true);
  });
});
