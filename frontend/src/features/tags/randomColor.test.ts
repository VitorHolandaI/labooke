import { describe, expect, it } from "vitest";

import { randomTagColor } from "./randomColor";

describe("randomTagColor", () => {
  it("returns a 6-digit hex color", () => {
    expect(randomTagColor()).toMatch(/^#[0-9a-f]{6}$/);
  });
});
