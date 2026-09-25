import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PdfZoomControls } from "./PdfZoomControls";

describe("PdfZoomControls", () => {
  it("shows the zoom as a percentage and wires each button", async () => {
    const user = userEvent.setup();
    const onZoomIn = vi.fn();
    const onZoomOut = vi.fn();
    const onReset = vi.fn();
    render(
      <PdfZoomControls zoom={1.25} onZoomIn={onZoomIn} onZoomOut={onZoomOut} onReset={onReset} />,
    );

    await user.click(screen.getByRole("button", { name: /aumentar zoom/i }));
    await user.click(screen.getByRole("button", { name: /diminuir zoom/i }));
    await user.click(screen.getByRole("button", { name: "125%" }));
    expect(onZoomIn).toHaveBeenCalledOnce();
    expect(onZoomOut).toHaveBeenCalledOnce();
    expect(onReset).toHaveBeenCalledOnce();
  });
});
