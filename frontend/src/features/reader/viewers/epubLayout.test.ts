import { describe, expect, it } from "vitest";

import { EPUB_SPREAD_MIN_WIDTH, epubSpread } from "./epubLayout";

describe("epubSpread", () => {
  it("maps the reader layout to an epubjs spread", () => {
    expect(epubSpread("single")).toBe("none");
    expect(epubSpread("double")).toBe("always");
  });

  // Regression: epubjs reads 0 as unset and falls back to an 800px minimum.
  it("uses a truthy minimum width so two pages always show", () => {
    expect(EPUB_SPREAD_MIN_WIDTH).toBeGreaterThan(0);
  });
});
