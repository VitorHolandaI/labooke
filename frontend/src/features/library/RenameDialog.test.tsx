import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { BookOut } from "../../api/books";
import { RenameDialog } from "./RenameDialog";

function book(overrides: Partial<BookOut> = {}): BookOut {
  return {
    id: 7,
    sha256: "deadbeef",
    title: "Old Title",
    author: null,
    format: "pdf",
    page_count: 100,
    status: "ready",
    ingest_error: null,
    tags: [],
    ...overrides,
  };
}

describe("RenameDialog", () => {
  it("renders with current book title pre-filled", () => {
    render(<RenameDialog book={book()} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("textbox", { name: /title/i })).toHaveValue("Old Title");
  });

  it("Save is disabled when title is unchanged", () => {
    render(<RenameDialog book={book()} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
  });

  it("Save is disabled when input is empty", async () => {
    const user = userEvent.setup();
    render(<RenameDialog book={book()} onSubmit={vi.fn()} onClose={vi.fn()} />);
    await user.clear(screen.getByRole("textbox", { name: /title/i }));
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
  });

  it("calls onSubmit with trimmed title on submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<RenameDialog book={book()} onSubmit={onSubmit} onClose={vi.fn()} />);
    const input = screen.getByRole("textbox", { name: /title/i });
    await user.clear(input);
    await user.type(input, "  New Title  ");
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit).toHaveBeenCalledWith("New Title");
  });

  it("shows error message when provided", () => {
    render(
      <RenameDialog book={book()} onSubmit={vi.fn()} onClose={vi.fn()} errorMessage="Save failed" />,
    );
    expect(screen.getByText("Save failed")).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<RenameDialog book={book()} onSubmit={vi.fn()} onClose={onClose} />);
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(<RenameDialog book={book()} onSubmit={vi.fn()} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
