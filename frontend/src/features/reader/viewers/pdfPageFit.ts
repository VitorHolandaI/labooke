export interface PageSize {
  width: number;
  height: number;
}

// Leaves a small margin so the page shadow is not clipped by the scroll box.
const FIT_MARGIN = 0.98;

/**
 * Scale that fits the whole page inside the available box.
 *
 * Example: `fitPageScale({ width: 595, height: 842 }, 1400, 800)` fits by height.
 */
export function fitPageScale(
  page: PageSize,
  availableWidth: number,
  availableHeight: number,
): number {
  const widthScale = availableWidth / page.width;
  if (availableHeight <= 0) return widthScale * FIT_MARGIN;
  return Math.min(widthScale, availableHeight / page.height) * FIT_MARGIN;
}
