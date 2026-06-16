import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateTagForm } from "./CreateTagForm";

describe("CreateTagForm", () => {
  it("Add tag button is disabled when name is empty", () => {
    render(<CreateTagForm onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /add tag/i })).toBeDisabled();
  });

  it("calls onSubmit with name, auto-generated slug, and default color", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<CreateTagForm onSubmit={onSubmit} />);
    await user.type(screen.getByRole("textbox", { name: /new tag name/i }), "Sci Fi");
    await user.click(screen.getByRole("button", { name: /add tag/i }));
    expect(onSubmit).toHaveBeenCalledWith({
      name: "Sci Fi",
      slug: "sci-fi",
      color: "#888888",
    });
  });

  it("clears the input after submission", async () => {
    const user = userEvent.setup();
    render(<CreateTagForm onSubmit={vi.fn()} />);
    const input = screen.getByRole("textbox", { name: /new tag name/i });
    await user.type(input, "fiction");
    await user.click(screen.getByRole("button", { name: /add tag/i }));
    expect(input).toHaveValue("");
  });

  it("disables button and shows Adding while isPending", () => {
    render(<CreateTagForm isPending onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: /adding/i })).toBeDisabled();
  });
});
