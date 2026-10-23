import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ZoomControls } from "./ZoomControls";

describe("ZoomControls", () => {
  it("shows the zoom as a percentage and wires each button", async () => {
    const user = userEvent.setup();
    const onZoomIn = vi.fn();
    const onZoomOut = vi.fn();
    const onReset = vi.fn();
    render(
      <ZoomControls
        zoom={1.25}
        resetTitle="Página inteira"
        onZoomIn={onZoomIn}
        onZoomOut={onZoomOut}
        onReset={onReset}
      />,
    );

    await user.click(screen.getByRole("button", { name: /aumentar zoom/i }));
    await user.click(screen.getByRole("button", { name: /diminuir zoom/i }));
    await user.click(screen.getByRole("button", { name: "125%" }));
    expect(onZoomIn).toHaveBeenCalledOnce();
    expect(onZoomOut).toHaveBeenCalledOnce();
    expect(onReset).toHaveBeenCalledOnce();
  });

  it("names what the reset goes back to", () => {
    render(
      <ZoomControls
        zoom={1}
        resetTitle="Fonte padrão"
        onZoomIn={vi.fn()}
        onZoomOut={vi.fn()}
        onReset={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "100%" })).toHaveAttribute(
      "title",
      "Fonte padrão (0)",
    );
  });
});
