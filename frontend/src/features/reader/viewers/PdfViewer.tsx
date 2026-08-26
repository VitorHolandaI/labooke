import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { useCallback, useEffect, useReducer, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import { PageJump } from "./PageJump";
import { PdfPageLayer } from "./PdfPageLayer";
import { PdfSearchControls } from "./PdfSearchControls";
import styles from "./PdfViewer.module.css";

GlobalWorkerOptions.workerSrc = PdfWorker;

type DocState =
  { phase: "loading" } | { phase: "ready"; total: number } | { phase: "error"; message: string };

type DocAction =
  { type: "load" } | { type: "ready"; total: number } | { type: "error"; message: string };

function docReducer(_: DocState, action: DocAction): DocState {
  switch (action.type) {
    case "load":
      return { phase: "loading" };
    case "ready":
      return { phase: "ready", total: action.total };
    case "error":
      return { phase: "error", message: action.message };
  }
}

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
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [page, setPage] = useState(initialPage);
  const [doc, dispatch] = useReducer(docReducer, { phase: "loading" });
  const [layout, setLayout] = useState<Layout>("single");
  const [fullscreen, setFullscreen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [containerSize, setContainerSize] = useState({ w: 0, h: 0 });
  // Callback ref: ResizeObserver is set up when the element actually mounts,
  // not at component mount (which happens while still in loading state).
  const [wrapEl, setWrapEl] = useState<HTMLDivElement | null>(null);

  const total = doc.phase === "ready" ? doc.total : 0;
  const step = layout === "double" ? 2 : 1;
  const goNext = useCallback(() => setPage((p) => Math.min(total, p + step)), [total, step]);
  const goPrev = useCallback(() => setPage((p) => Math.max(1, p - step)), [step]);
  const { onTouchStart, onTouchMove, onTouchEnd } = useSwipeGesture(goNext, goPrev);

  // ResizeObserver — wrapEl dep ensures this runs when canvasWrap enters DOM
  useEffect(() => {
    if (!wrapEl) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setContainerSize({ w: width, h: height });
    });
    ro.observe(wrapEl);
    return () => ro.disconnect();
  }, [wrapEl]);

  // Load PDF document
  useEffect(() => {
    let cancelled = false;
    let loadedPdf: PDFDocumentProxy | null = null;
    dispatch({ type: "load" });
    const task = getDocument({ url: bookFileUrl(bookId) });
    task.promise
      .then((nextPdf) => {
        if (cancelled) {
          nextPdf.destroy();
          return;
        }
        loadedPdf = nextPdf;
        setPdf(nextPdf);
        dispatch({ type: "ready", total: nextPdf.numPages });
      })
      .catch((err) => {
        if (!cancelled) dispatch({ type: "error", message: (err as Error).message });
      });
    return () => {
      cancelled = true;
      void loadedPdf?.destroy();
    };
  }, [bookId]);

  // Notify parent of page changes
  useEffect(() => {
    if (total > 0) onPageChange?.(Math.min(page, total));
  }, [page, total, onPageChange]);

  // Keyboard navigation
  useEffect(() => {
    if (total === 0) return;
    const onKey = (e: KeyboardEvent) => {
      const target = e.target;
      if (
        target instanceof HTMLElement &&
        (target.matches("input, textarea, select") || target.isContentEditable)
      )
        return;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        goNext();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "Escape" && fullscreen) {
        setFullscreen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total, goNext, goPrev, fullscreen]);

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
            query={searchQuery}
          />
        )}
        {pdf && secondVisible && (
          <PdfPageLayer
            pdf={pdf}
            pageNumber={page + 1}
            availableWidth={pageWidth}
            availableHeight={containerSize.h}
            query={searchQuery}
          />
        )}
      </div>
    </div>
  );
}
