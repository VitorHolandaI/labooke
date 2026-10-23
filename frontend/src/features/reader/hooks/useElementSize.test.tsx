import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { useElementSize } from "./useElementSize";

// jsdom has no ResizeObserver; this one lets the test fire resizes by hand.
class FakeResizeObserver {
  static latest: FakeResizeObserver | null = null;
  observed: Element | null = null;
  disconnected = false;

  constructor(private readonly callback: ResizeObserverCallback) {
    FakeResizeObserver.latest = this;
  }

  observe(target: Element): void {
    this.observed = target;
  }

  disconnect(): void {
    this.disconnected = true;
  }

  resizeTo(width: number, height: number): void {
    const entry = { contentRect: { width, height } } as ResizeObserverEntry;
    this.callback([entry], this as unknown as ResizeObserver);
  }
}

const realResizeObserver = globalThis.ResizeObserver;

afterEach(() => {
  globalThis.ResizeObserver = realResizeObserver;
  FakeResizeObserver.latest = null;
});

describe("useElementSize", () => {
  it("reports zero until an element mounts", () => {
    globalThis.ResizeObserver = FakeResizeObserver as unknown as typeof ResizeObserver;
    const { result } = renderHook(() => useElementSize(null));
    expect(result.current).toEqual({ w: 0, h: 0 });
    expect(FakeResizeObserver.latest).toBeNull();
  });

  // Regression: fullscreen only swaps a CSS class, so no window resize fires.
  it("follows the element's own size changes", () => {
    globalThis.ResizeObserver = FakeResizeObserver as unknown as typeof ResizeObserver;
    const el = document.createElement("div");
    const { result, unmount } = renderHook(() => useElementSize(el));
    expect(FakeResizeObserver.latest?.observed).toBe(el);

    act(() => FakeResizeObserver.latest?.resizeTo(1280, 720));
    expect(result.current).toEqual({ w: 1280, h: 720 });

    unmount();
    expect(FakeResizeObserver.latest?.disconnected).toBe(true);
  });
});
