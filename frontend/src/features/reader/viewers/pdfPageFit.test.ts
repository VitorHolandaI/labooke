import { describe, expect, it } from "vitest";

import { fitPageScale } from "./pdfPageFit";

const A4 = { width: 595, height: 842 };

describe("fitPageScale", () => {
  // Regression: using the larger scale cropped pages on landscape laptops.
  it("fits by height when the box is wider than the page", () => {
    const scale = fitPageScale(A4, 1400, 800);
    expect(A4.height * scale).toBeLessThanOrEqual(800);
    expect(A4.width * scale).toBeLessThanOrEqual(1400);
    expect(A4.height * scale).toBeGreaterThan(760);
  });

  it("fits by width when the box is narrower than the page", () => {
    const scale = fitPageScale(A4, 400, 1000);
    expect(A4.width * scale).toBeLessThanOrEqual(400);
    expect(A4.width * scale).toBeGreaterThan(380);
  });

  it("falls back to width when the height is not measured yet", () => {
    const scale = fitPageScale(A4, 595, 0);
    expect(A4.width * scale).toBeLessThanOrEqual(595);
    expect(A4.width * scale).toBeGreaterThan(565);
  });
});
