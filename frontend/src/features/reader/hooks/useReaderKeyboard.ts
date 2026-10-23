import { useEffect, useRef } from "react";

import { isEditableTarget } from "../viewers/editableTarget";

export interface ReaderKeyActions {
  next: () => void;
  prev: () => void;
  exitFullscreen: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
}

type KeyPress = Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey">;

const KEY_TO_ACTION: Record<string, keyof ReaderKeyActions> = {
  ArrowRight: "next",
  ArrowDown: "next",
  ArrowLeft: "prev",
  ArrowUp: "prev",
  Escape: "exitFullscreen",
  "+": "zoomIn",
  "=": "zoomIn",
  "-": "zoomOut",
  "0": "resetZoom",
};

/**
 * The reader action a key press triggers, or null when the key isn't ours.
 *
 * Example: `readerKeyAction(event, actions)?.()`.
 */
export function readerKeyAction(press: KeyPress, actions: ReaderKeyActions): (() => void) | null {
  // Ctrl/Cmd +/- is the browser's own zoom; don't stack ours on it.
  if (press.ctrlKey || press.metaKey) return null;
  const name = KEY_TO_ACTION[press.key];
  return name ? actions[name] : null;
}

/**
 * Binds the shared reader shortcuts to the window while `enabled`.
 *
 * Example: `useReaderKeyboard({ next, prev, ... }, total > 0);`
 */
export function useReaderKeyboard(actions: ReaderKeyActions, enabled: boolean): void {
  // Ref so callers can pass a fresh object each render without re-binding.
  const actionsRef = useRef(actions);
  useEffect(() => {
    actionsRef.current = actions;
  });

  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (isEditableTarget(e.target)) return;
      const action = readerKeyAction(e, actionsRef.current);
      if (!action) return;
      e.preventDefault();
      action();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enabled]);
}
