import { describe, expect, it } from "vitest";

import { isEditableTarget } from "./editableTarget";

describe("isEditableTarget", () => {
  it("is true for form fields so typing a page number doesn't zoom", () => {
    expect(isEditableTarget(document.createElement("input"))).toBe(true);
    expect(isEditableTarget(document.createElement("textarea"))).toBe(true);
  });

  it("is false for the page itself and for non-elements", () => {
    expect(isEditableTarget(document.createElement("div"))).toBe(false);
    expect(isEditableTarget(window)).toBe(false);
    expect(isEditableTarget(null)).toBe(false);
  });
});
