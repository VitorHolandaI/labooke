import { useCallback, useState } from "react";

import { parseStoredZoom, stepZoom } from "../viewers/readerZoom";

// The PDF key predates the other formats; renaming it would drop saved zooms.
export const PDF_ZOOM_KEY = "labooke.pdfZoom";
export const EPUB_ZOOM_KEY = "labooke.epubZoom";
export const TEXT_ZOOM_KEY = "labooke.textZoom";

export type ZoomStorage = Pick<Storage, "getItem" | "setItem">;

export interface ReaderZoom {
  zoom: number;
  zoomIn: () => void;
  zoomOut: () => void;
  resetZoom: () => void;
}

/**
 * Zoom level remembered per browser and format, so a laptop keeps its setting.
 *
 * Example: `const { zoom, zoomIn } = useReaderZoom(PDF_ZOOM_KEY);`
 */
export function useReaderZoom(
  storageKey: string,
  storage: ZoomStorage = window.localStorage,
): ReaderZoom {
  const [zoom, setZoom] = useState(() => parseStoredZoom(storage.getItem(storageKey)));

  const applyZoom = useCallback(
    (next: number) => {
      setZoom(next);
      storage.setItem(storageKey, String(next));
    },
    [storage, storageKey],
  );

  // Stable callbacks keep the viewer's keydown listener from re-binding.
  const zoomIn = useCallback(() => applyZoom(stepZoom(zoom, 1)), [applyZoom, zoom]);
  const zoomOut = useCallback(() => applyZoom(stepZoom(zoom, -1)), [applyZoom, zoom]);
  const resetZoom = useCallback(() => applyZoom(1), [applyZoom]);
  return { zoom, zoomIn, zoomOut, resetZoom };
}
