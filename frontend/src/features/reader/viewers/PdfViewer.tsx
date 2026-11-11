import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { useCallback, useEffect, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useElementSize } from "../hooks/useElementSize";
import { usePdfDocument } from "../hooks/usePdfDocument";
import { useReaderKeyboard } from "../hooks/useReaderKeyboard";
import { PDF_ZOOM_KEY, useReaderZoom } from "../hooks/useReaderZoom";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import { PageJump } from "./PageJump";
import { PdfPageLayer } from "./PdfPageLayer";
import { PdfSearchControls } from "./PdfSearchControls";
import styles from "./PdfViewer.module.css";
import { ZoomControls } from "./ZoomControls";

GlobalWorkerOptions.workerSrc = PdfWorker;

type Layout = "single" | "double";

interface Props {
  bookId: number;
  initialPage?: number;
  onPageChange?: (page: number) => void;
  isBookmarked?: boolean;
  onAddBookmark?: () => void;
}

export function PdfViewer({
  bookId,
  initialPage = 1,
  onPageChange,
  isBookmarked,
  onAddBookmark,
}: Props) {
  const { pdf, state: doc } = usePdfDocument(bookFileUrl(bookId), getDocument);
  const [page, setPage] = useState(initialPage);
  const [layout, setLayout] = useState<Layout>("single");
  const [fullscreen, setFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const { zoom, zoomIn, zoomOut, resetZoom } = useReaderZoom(PDF_ZOOM_KEY);
  // Callback ref: ResizeObserver is set up when the element actually mounts,
  // not at component mount (which happens while still in loading state).
  const [wrapEl, setWrapEl] = useState<HTMLDivElement | null>(null);
  const containerSize = useElementSize(wrapEl);

  const total = doc.phase === "ready" ? doc.total : 0;
  const step = layout === "double" ? 2 : 1;
  const goNext = useCallback(() => setPage((p) => Math.min(total, p + step)), [total, step]);
  const goPrev = useCallback(() => setPage((p) => Math.max(1, p - step)), [step]);
  const { onTouchStart, onTouchMove, onTouchEnd } = useSwipeGesture(goNext, goPrev);

  // Notify parent of page changes
  useEffect(() => {
    if (total > 0) onPageChange?.(Math.min(page, total));
  }, [page, total, onPageChange]);

  const exitFullscreen = useCallback(() => setFullscreen(false), []);
  useReaderKeyboard(
    { next: goNext, prev: goPrev, exitFullscreen, zoomIn, zoomOut, resetZoom },
    total > 0,
  );

  // Tap left/right edges to navigate (mobile-friendly)
  const handleCanvasAreaClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target instanceof Element && e.target.closest('[data-pdf-text-layer="true"]')) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width;
      if (relX < 0.25) goPrev();
      else if (relX > 0.75) goNext();
    },
    [goPrev, goNext],
  );
  const handleTouchStart = useCallback(
    (event: React.TouchEvent<HTMLDivElement>) => {
      if (event.target instanceof Element && event.target.closest('[data-pdf-text-layer="true"]'))
        return;
      onTouchStart(event);
    },
    [onTouchStart],
  );

  if (doc.phase === "error")
    return <div className={styles.error}>Failed to load: {doc.message}</div>;
  if (doc.phase === "loading") return <div className={styles.loading}>Loading PDF…</div>;

  const secondVisible = layout === "double" && page + 1 <= total;
  const counterLabel = secondVisible ? `${page}–${page + 1} / ${total}` : `${page} / ${total}`;
  const pageWidth = layout === "double" ? Math.floor(containerSize.w / 2) - 8 : containerSize.w;
  return (
    <div className={fullscreen ? styles.wrapFull : styles.wrap}>
      <div className={styles.controls}>
        <button type="button" disabled={page <= 1} onClick={goPrev}>
          ←
        </button>
        <span className={styles.counter}>{counterLabel}</span>
        <PageJump current={page} total={total} onJump={setPage} />
        <button type="button" disabled={page + step - 1 >= total} onClick={goNext}>
          →
        </button>
        <div className={styles.controlsSep} />
        <ZoomControls
          zoom={zoom}
          resetTitle="Página inteira"
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onReset={resetZoom}
        />
        {onAddBookmark && (
          <button
            type="button"
            className={isBookmarked ? styles.ctrlActive : styles.ctrl}
            onClick={onAddBookmark}
            disabled={isBookmarked}
            title={isBookmarked ? "Página já marcada" : "Marcar página"}
          >
            {isBookmarked ? "★" : "☆"}
          </button>
        )}
        <button
          type="button"
          className={`${layout === "double" ? styles.ctrlActive : styles.ctrl} ${styles.ctrlDesktop}`}
          onClick={() => setLayout((l) => (l === "single" ? "double" : "single"))}
          title="Alternar entre 1 e 2 páginas"
        >
          {layout === "single" ? "⊟ 2 pág." : "⊞ 1 pág."}
        </button>
        <button
          type="button"
          className={fullscreen ? styles.ctrlActive : styles.ctrl}
          onClick={() => setFullscreen((f) => !f)}
          title={fullscreen ? "Sair da tela cheia (Esc)" : "Tela cheia"}
        >
          {fullscreen ? "⊠" : "⛶"}
        </button>
      </div>
      {pdf && (
        <PdfSearchControls
          pdf={pdf}
          currentPage={page}
          onJump={setPage}
          onQueryChange={setSearchQuery}
        />
      )}
      <div
        className={layout === "double" ? styles.canvasWrapDouble : styles.canvasWrap}
        ref={setWrapEl}
        onClick={handleCanvasAreaClick}
        onTouchStart={handleTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {pdf && (
          <PdfPageLayer
            pdf={pdf}
            pageNumber={page}
            availableWidth={pageWidth}
            availableHeight={containerSize.h}
            zoom={zoom}
            query={searchQuery}
          />
        )}
        {pdf && secondVisible && (
          <PdfPageLayer
            pdf={pdf}
            pageNumber={page + 1}
            availableWidth={pageWidth}
            availableHeight={containerSize.h}
            zoom={zoom}
            query={searchQuery}
          />
        )}
      </div>
    </div>
  );
}
