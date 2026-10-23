import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { readerKeyAction, useReaderKeyboard, type ReaderKeyActions } from "./useReaderKeyboard";

class RecordingKeyActions implements ReaderKeyActions {
  readonly calls: string[] = [];
  next = (): void => void this.calls.push("next");
  prev = (): void => void this.calls.push("prev");
  exitFullscreen = (): void => void this.calls.push("exitFullscreen");
  zoomIn = (): void => void this.calls.push("zoomIn");
  zoomOut = (): void => void this.calls.push("zoomOut");
  resetZoom = (): void => void this.calls.push("resetZoom");
}

function key(k: string, mods: Partial<Pick<KeyboardEvent, "ctrlKey" | "metaKey">> = {}) {
  return { key: k, ctrlKey: false, metaKey: false, ...mods };
}

describe("readerKeyAction", () => {
  it("maps arrows, Escape and the zoom keys", () => {
    const actions = new RecordingKeyActions();
    for (const k of [
      "ArrowRight",
      "ArrowDown",
      "ArrowLeft",
      "ArrowUp",
      "Escape",
      "+",
      "=",
      "-",
      "0",
    ]) {
      readerKeyAction(key(k), actions)?.();
    }
    expect(actions.calls).toEqual([
      "next",
      "next",
      "prev",
      "prev",
      "exitFullscreen",
      "zoomIn",
      "zoomIn",
      "zoomOut",
      "resetZoom",
    ]);
  });

  it("leaves Ctrl/Cmd zoom and unknown keys to the browser", () => {
    const actions = new RecordingKeyActions();
    expect(readerKeyAction(key("+", { ctrlKey: true }), actions)).toBeNull();
    expect(readerKeyAction(key("0", { metaKey: true }), actions)).toBeNull();
    expect(readerKeyAction(key("a"), actions)).toBeNull();
  });
});

describe("useReaderKeyboard", () => {
  it("runs the action for a window keydown", () => {
    const actions = new RecordingKeyActions();
    renderHook(() => useReaderKeyboard(actions, true));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    expect(actions.calls).toEqual(["next"]);
  });

  it("ignores keys typed into a field, like the page jump box", () => {
    const actions = new RecordingKeyActions();
    renderHook(() => useReaderKeyboard(actions, true));
    const input = document.createElement("input");
    document.body.append(input);
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "0", bubbles: true }));
    input.remove();
    expect(actions.calls).toEqual([]);
  });

  it("does nothing while disabled", () => {
    const next = vi.fn();
    renderHook(() => useReaderKeyboard({ ...new RecordingKeyActions(), next }, false));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    expect(next).not.toHaveBeenCalled();
  });
});
