import { useEffect, useState } from "react";

export interface ElementSize {
  w: number;
  h: number;
}

/**
 * Live content size of an element, following its own resizes rather than the
 * window's (fullscreen and layout toggles only change CSS).
 *
 * Example: `const size = useElementSize(wrapEl);`
 */
export function useElementSize(el: HTMLElement | null): ElementSize {
  const [size, setSize] = useState<ElementSize>({ w: 0, h: 0 });
  useEffect(() => {
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setSize({ w: width, h: height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [el]);
  return size;
}
