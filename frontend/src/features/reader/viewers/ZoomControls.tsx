import { ZOOM_MAX, ZOOM_MIN } from "./readerZoom";
import styles from "./ZoomControls.module.css";

interface Props {
  zoom: number;
  /** What the percentage button goes back to, e.g. "Página inteira". */
  resetTitle: string;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
}

/** Zoom buttons shared by every reader toolbar; the percentage resets to 100%. */
export function ZoomControls({ zoom, resetTitle, onZoomIn, onZoomOut, onReset }: Props) {
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
      <button type="button" onClick={onReset} title={`${resetTitle} (0)`}>
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
