import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { TagOut } from "../../api/tags";
import { EditTagDialog } from "./EditTagDialog";

const TAG: TagOut = { id: 1, name: "fiction", slug: "fiction", color: "#ff0000" };

describe("EditTagDialog", () => {
  it("renders with current name and color pre-filled", () => {
    render(<EditTagDialog tag={TAG} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("textbox", { name: /name/i })).toHaveValue("fiction");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("Save is disabled when nothing changed", () => {
    render(<EditTagDialog tag={TAG} onSubmit={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
  });

  it("calls onSubmit with trimmed name when name changes", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<EditTagDialog tag={TAG} onSubmit={onSubmit} onClose={vi.fn()} />);
    const input = screen.getByRole("textbox", { name: /name/i });
    await user.clear(input);
    await user.type(input, "  sci-fi  ");
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(onSubmit).toHaveBeenCalledWith({ name: "sci-fi", color: TAG.color });
  });

  it("shows error message when provided", () => {
    render(
      <EditTagDialog tag={TAG} onSubmit={vi.fn()} onClose={vi.fn()} errorMessage="Server error" />,
    );
    expect(screen.getByText("Server error")).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<EditTagDialog tag={TAG} onSubmit={vi.fn()} onClose={onClose} />);
    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose on Escape key", () => {
    const onClose = vi.fn();
    render(<EditTagDialog tag={TAG} onSubmit={vi.fn()} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
