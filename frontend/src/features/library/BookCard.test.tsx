import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { BookOut } from "../../api/books";
import { BookCard } from "./BookCard";

function book(overrides: Partial<BookOut> = {}): BookOut {
  return {
    id: 7,
    sha256: "deadbeef",
    title: "The Test Book",
    author: "Pat Pytest",
    format: "pdf",
    page_count: 200,
    status: "ready",
    ingest_error: null,
    tags: [{ id: 1, name: "fiction", slug: "fiction", color: "#aaa" }],
    ...overrides,
  };
}

function renderCard(b: BookOut) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <BookCard book={b} allTags={[]} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BookCard", () => {
  it("links to the details page when status is ready", () => {
    renderCard(book());
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThan(0);
    expect(links[0]).toHaveAttribute("href", "/book/7");
  });

  it("shows the ingest badge while pending and disables the link", () => {
    renderCard(book({ status: "pending", title: "Half-In Book" }));
    expect(screen.getByText(/ingesting/i)).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("shows failure message when status is failed", () => {
    renderCard(book({ status: "failed", ingest_error: "encrypted PDF" }));
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
    expect(screen.getByText("encrypted PDF")).toBeInTheDocument();
  });
});
