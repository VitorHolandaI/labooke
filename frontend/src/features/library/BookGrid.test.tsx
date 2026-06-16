import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { BookOut } from "../../api/books";
import { BookGrid } from "./BookGrid";

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

function book(id: number, overrides: Partial<BookOut> = {}): BookOut {
  return {
    id,
    sha256: `sha${id}`,
    title: `Book ${id}`,
    author: null,
    format: "pdf",
    page_count: 10,
    status: "ready",
    ingest_error: null,
    tags: [],
    ...overrides,
  };
}

describe("BookGrid", () => {
  it("shows loading state", () => {
    render(<BookGrid books={[]} allTags={[]} isLoading={true} isError={false} />, { wrapper });
    expect(screen.getByText(/loading library/i)).toBeInTheDocument();
  });

  it("shows error state", () => {
    render(<BookGrid books={[]} allTags={[]} isLoading={false} isError={true} />, { wrapper });
    expect(screen.getByText(/could not load books/i)).toBeInTheDocument();
  });

  it("shows empty message when no books", () => {
    render(<BookGrid books={[]} allTags={[]} isLoading={false} isError={false} />, { wrapper });
    expect(screen.getByText(/no books match/i)).toBeInTheDocument();
  });

  it("renders a card per book", () => {
    const books = [book(1), book(2), book(3)];
    render(<BookGrid books={books} allTags={[]} isLoading={false} isError={false} />, { wrapper });
    expect(screen.getByText("Book 1")).toBeInTheDocument();
    expect(screen.getByText("Book 2")).toBeInTheDocument();
    expect(screen.getByText("Book 3")).toBeInTheDocument();
  });
});
