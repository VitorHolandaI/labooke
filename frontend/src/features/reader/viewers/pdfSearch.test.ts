import { describe, expect, it } from "vitest";

import type { PdfSearchDocument, PdfSearchPage } from "./pdfSearch";
import { normalizePdfText, searchPdfDocument } from "./pdfSearch";

class FakePdfPage implements PdfSearchPage {
  constructor(private readonly strings: string[]) {}

  async getTextContent(): Promise<{ items: readonly unknown[] }> {
    return { items: this.strings.map((str) => ({ str })) };
  }
}

class FakePdfDocument implements PdfSearchDocument {
  readonly numPages: number;

  constructor(private readonly pages: string[][]) {
    this.numPages = pages.length;
  }

  async getPage(pageNumber: number): Promise<PdfSearchPage> {
    return new FakePdfPage(this.pages[pageNumber - 1]);
  }
}

describe("PDF text search", () => {
  it("normalizes accents, case and line-break hyphenation", () => {
    expect(normalizePdfText("  PROGRAMA-\nÇÃO  ")).toBe("programacao");
  });

  it("returns match counts grouped by page", async () => {
    const pdf = new FakePdfDocument([
      ["Programação funcional e programação web"],
      ["Outro assunto"],
      ["PROGRAMA-\nÇÃO concorrente"],
    ]);

    await expect(searchPdfDocument(pdf, "programação")).resolves.toEqual({
      hits: [
        { page: 1, matches: 2 },
        { page: 3, matches: 1 },
      ],
      matches: 3,
    });
  });
});
