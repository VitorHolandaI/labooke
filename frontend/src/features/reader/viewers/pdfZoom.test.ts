import { describe, expect, it } from "vitest";

import { ZOOM_MAX, ZOOM_MIN, parseStoredZoom, stepZoom } from "./pdfZoom";

describe("stepZoom", () => {
  it("moves one step in the given direction", () => {
    expect(stepZoom(1, 1)).toBe(1.25);
    expect(stepZoom(1, -1)).toBe(0.75);
  });

  it("clamps to the allowed range", () => {
    expect(stepZoom(ZOOM_MAX, 1)).toBe(ZOOM_MAX);
    expect(stepZoom(ZOOM_MIN, -1)).toBe(ZOOM_MIN);
  });
});

describe("parseStoredZoom", () => {
  it("reads a stored zoom inside the range", () => {
    expect(parseStoredZoom("1.5")).toBe(1.5);
  });

  it("falls back to fit-page for missing or invalid values", () => {
    expect(parseStoredZoom(null)).toBe(1);
    expect(parseStoredZoom("abc")).toBe(1);
    expect(parseStoredZoom("99")).toBe(1);
  });
});
