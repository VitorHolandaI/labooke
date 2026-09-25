import { useCallback, useState } from "react";

import { parseStoredZoom, stepZoom } from "../viewers/pdfZoom";

export const PDF_ZOOM_KEY = "labooke.pdfZoom";

export type ZoomStorage = Pick<Storage, "getItem" | "setItem">;

export interface PdfZoom {
  zoom: number;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
}

/**
 * PDF zoom level remembered per browser, so a laptop keeps its setting.
 *
 * Example: `const { zoom, zoomIn } = usePdfZoom();`
 */
export function usePdfZoom(storage: ZoomStorage = window.localStorage): PdfZoom {
  const [zoom, setZoom] = useState(() => parseStoredZoom(storage.getItem(PDF_ZOOM_KEY)));

  const applyZoom = useCallback(
    (next: number) => {
      setZoom(next);
      storage.setItem(PDF_ZOOM_KEY, String(next));
    },
    [storage],
  );

  // Stable callbacks keep the viewer's keydown listener from re-binding.
  const zoomIn = useCallback(() => applyZoom(stepZoom(zoom, 1)), [applyZoom, zoom]);
  const zoomOut = useCallback(() => applyZoom(stepZoom(zoom, -1)), [applyZoom, zoom]);
  const resetZoom = useCallback(() => applyZoom(1), [applyZoom]);
  return { zoom, zoomIn, zoomOut, resetZoom };
}
