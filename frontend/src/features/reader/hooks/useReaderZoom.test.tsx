import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EPUB_ZOOM_KEY, PDF_ZOOM_KEY, useReaderZoom, type ZoomStorage } from "./useReaderZoom";

class FakeZoomStorage implements ZoomStorage {
  readonly saved = new Map<string, string>();

  getItem(key: string): string | null {
    return this.saved.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.saved.set(key, value);
  }
}

describe("useReaderZoom", () => {
  it("starts from the stored zoom", () => {
    const storage = new FakeZoomStorage();
    storage.setItem(PDF_ZOOM_KEY, "1.5");
    const { result } = renderHook(() => useReaderZoom(PDF_ZOOM_KEY, storage));
    expect(result.current.zoom).toBe(1.5);
  });

  it("persists each change so the laptop keeps its zoom", () => {
    const storage = new FakeZoomStorage();
    const { result } = renderHook(() => useReaderZoom(PDF_ZOOM_KEY, storage));
    act(() => result.current.zoomIn());
    expect(result.current.zoom).toBe(1.25);
    expect(storage.getItem(PDF_ZOOM_KEY)).toBe("1.25");
    act(() => result.current.resetZoom());
    expect(storage.getItem(PDF_ZOOM_KEY)).toBe("1");
  });

  // Page zoom and font zoom mean different things, so each format keeps its own.
  it("keeps each format's zoom apart", () => {
    const storage = new FakeZoomStorage();
    const { result } = renderHook(() => useReaderZoom(EPUB_ZOOM_KEY, storage));
    act(() => result.current.zoomIn());
    expect(storage.getItem(EPUB_ZOOM_KEY)).toBe("1.25");
    expect(storage.getItem(PDF_ZOOM_KEY)).toBeNull();
  });
});
