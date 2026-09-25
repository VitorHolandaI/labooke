import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PDF_ZOOM_KEY, usePdfZoom, type ZoomStorage } from "./usePdfZoom";

class FakeZoomStorage implements ZoomStorage {
  readonly saved = new Map<string, string>();

  getItem(key: string): string | null {
    return this.saved.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.saved.set(key, value);
  }
}

describe("usePdfZoom", () => {
  it("starts from the stored zoom", () => {
    const storage = new FakeZoomStorage();
    storage.setItem(PDF_ZOOM_KEY, "1.5");
    const { result } = renderHook(() => usePdfZoom(storage));
    expect(result.current.zoom).toBe(1.5);
  });

  it("persists each change so the laptop keeps its zoom", () => {
    const storage = new FakeZoomStorage();
    const { result } = renderHook(() => usePdfZoom(storage));
    act(() => result.current.zoomIn());
    expect(result.current.zoom).toBe(1.25);
    expect(storage.getItem(PDF_ZOOM_KEY)).toBe("1.25");
    act(() => result.current.resetZoom());
    expect(storage.getItem(PDF_ZOOM_KEY)).toBe("1");
  });
});
