import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import type { BookOut } from "../../api/books";
import type { TagOut } from "../../api/tags";
import { TagsEditDialog } from "./TagsEditDialog";

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const TAG_FICTION: TagOut = { id: 1, name: "fiction", slug: "fiction", color: "#f00" };
const TAG_LINUX: TagOut = { id: 2, name: "linux", slug: "linux", color: "#0f0" };

function book(tags: TagOut[] = []): BookOut {
  return {
    id: 7,
    sha256: "x",
    title: "Test Book",
    author: null,
    format: "pdf",
    page_count: 1,
    status: "ready",
    ingest_error: null,
    tags,
  };
}

describe("TagsEditDialog", () => {
  it("renders all tags with correct checked state", () => {
    render(
      <TagsEditDialog
        book={book([TAG_FICTION])}
        allTags={[TAG_FICTION, TAG_LINUX]}
        onToggle={vi.fn()}
        onClose={vi.fn()}
      />,
      { wrapper },
    );
    const [fictionBox, linuxBox] = screen.getAllByRole("checkbox");
    expect(fictionBox).toBeChecked();
    expect(linuxBox).not.toBeChecked();
  });

  it("calls onToggle(tag, true) when an attached tag checkbox is clicked", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    render(
      <TagsEditDialog
        book={book([TAG_FICTION])}
        allTags={[TAG_FICTION]}
        onToggle={onToggle}
        onClose={vi.fn()}
      />,
      { wrapper },
    );
    await user.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith(TAG_FICTION, true);
  });

  it("calls onToggle(tag, false) when a detached tag checkbox is clicked", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    render(
      <TagsEditDialog
        book={book([])}
        allTags={[TAG_FICTION]}
        onToggle={onToggle}
        onClose={vi.fn()}
      />,
      { wrapper },
    );
    await user.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith(TAG_FICTION, false);
  });

  it("shows empty message when no tags exist", () => {
    render(
      <TagsEditDialog book={book()} allTags={[]} onToggle={vi.fn()} onClose={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText(/no tags yet/i)).toBeInTheDocument();
  });

  it("calls onClose when Done is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <TagsEditDialog book={book()} allTags={[]} onToggle={vi.fn()} onClose={onClose} />,
      { wrapper },
    );
    await user.click(screen.getByRole("button", { name: /done/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
