import { ZOOM_MAX, ZOOM_MIN } from "./pdfZoom";
import styles from "./PdfViewer.module.css";

interface Props {
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}

/** Zoom buttons for the PDF toolbar; the percentage resets to fit-page. */
export function PdfZoomControls({ zoom, onZoomIn, onZoomOut, onReset }: Props) {
  return (
    <div className={styles.zoom}>
      <button
        type="button"
        onClick={onZoomOut}
        disabled={zoom <= ZOOM_MIN}
        aria-label="Diminuir zoom"
        title="Diminuir zoom (-)"
      >
        −
      </button>
      <button type="button" onClick={onReset} title="Página inteira (0)">
        {Math.round(zoom * 100)}%
      </button>
      <button
        type="button"
        onClick={onZoomIn}
        disabled={zoom >= ZOOM_MAX}
        aria-label="Aumentar zoom"
        title="Aumentar zoom (+)"
      >
        +
      </button>
    </div>
  );
}
