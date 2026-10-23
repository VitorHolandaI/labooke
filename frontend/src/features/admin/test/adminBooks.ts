import type { BookOut } from "../../../api/books";

/** A library book as the admin lists see it; override what a test cares about. */
export function adminBook(overrides: Partial<BookOut> = {}): BookOut {
  return {
    id: 7,
    sha256: "book-7",
    title: "Sistemas Distribuídos",
    author: null,
    description: "Consenso, replicação e tolerância a falhas.",
    format: "pdf",
    page_count: 200,
    status: "ready",
    ingest_error: null,
    auto_tagged_at: null,
    tags: [],
    ...overrides,
  };
}
