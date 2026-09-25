// Zoom multiplies the fit-page scale, so 1 always means "whole page visible".
export const ZOOM_MIN = 0.5;
export const ZOOM_MAX = 3;
export const ZOOM_STEP = 0.25;

/**
 * Next zoom level one step up (1) or down (-1), clamped to the range.
 *
 * Example: `stepZoom(1, 1)` returns `1.25`.
 */
export function stepZoom(current: number, direction: 1 | -1): number {
  const next = Math.round((current + direction * ZOOM_STEP) * 100) / 100;
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, next));
}

/**
 * Zoom read back from storage, or 1 when absent or out of range.
 *
 * Example: `parseStoredZoom("1.5")` returns `1.5`.
 */
export function parseStoredZoom(raw: string | null): number {
  const value = Number(raw);
  if (raw === null || !Number.isFinite(value)) return 1;
  if (value < ZOOM_MIN || value > ZOOM_MAX) return 1;
  return value;
}
