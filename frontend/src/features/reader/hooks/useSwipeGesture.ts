import { useCallback, useRef } from "react";

export function useSwipeGesture(onNext: () => void, onPrev: () => void) {
  const startX = useRef<number | null>(null);
  const startY = useRef<number | null>(null);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    // Ignore multi-touch (pinch zoom)
    if (e.touches.length !== 1) { startX.current = null; return; }
    startX.current = e.touches[0].clientX;
    startY.current = e.touches[0].clientY;
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    // Cancel if a second finger is added mid-gesture
    if (e.touches.length > 1) { startX.current = null; }
  }, []);

  const onTouchEnd = useCallback((e: React.TouchEvent) => {
    if (startX.current === null) return;
    const deltaX = e.changedTouches[0].clientX - startX.current;
    const deltaY = e.changedTouches[0].clientY - (startY.current ?? 0);
    startX.current = null;
    startY.current = null;
    // Ignore if mostly vertical (scrolling)
    if (Math.abs(deltaY) > Math.abs(deltaX) * 0.8) return;
    if (Math.abs(deltaX) < 60) return;
    if (deltaX < 0) onNext(); else onPrev();
  }, [onNext, onPrev]);

  return { onTouchStart, onTouchMove, onTouchEnd };
}
