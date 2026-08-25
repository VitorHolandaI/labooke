import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PdfSearchControls } from "./PdfSearchControls";
import type { PdfSearchDocument, PdfSearchPage } from "./pdfSearch";

class FakeSearchPage implements PdfSearchPage {
  constructor(private readonly text: string) {}

  async getTextContent(): Promise<{ items: readonly unknown[] }> {
    return { items: [{ str: this.text }] };
  }
}

class FakeSearchDocument implements PdfSearchDocument {
  readonly numPages: number;

  constructor(private readonly pages: string[]) {
    this.numPages = pages.length;
  }

  async getPage(pageNumber: number): Promise<PdfSearchPage> {
    return new FakeSearchPage(this.pages[pageNumber - 1]);
  }
}

describe("PdfSearchControls", () => {
  it("searches the document and navigates between matching pages", async () => {
    const user = userEvent.setup();
    const onJump = vi.fn();
    const onQueryChange = vi.fn();
    const pdf = new FakeSearchDocument(["capa", "uma bússola", "outra bussola"]);
    render(
      <PdfSearchControls pdf={pdf} currentPage={1} onJump={onJump} onQueryChange={onQueryChange} />,
    );

    await user.type(screen.getByRole("searchbox", { name: /buscar palavra/i }), "bússola{Enter}");
    expect(await screen.findByText("2 ocorrências em 2 páginas")).toBeInTheDocument();
    expect(onQueryChange).toHaveBeenCalledWith("bússola");
    expect(onJump).toHaveBeenCalledWith(2);

    await user.click(screen.getByRole("button", { name: /próximo resultado/i }));
    expect(onJump).toHaveBeenLastCalledWith(3);
  });
});
