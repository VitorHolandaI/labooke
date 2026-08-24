import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import { PageJump } from "./PageJump";
import styles from "./PdfViewer.module.css";

GlobalWorkerOptions.workerSrc = PdfWorker;

type DocState =
  | { phase: "loading" }
  | { phase: "ready"; total: number }
  | { phase: "error"; message: string };

type DocAction =
  | { type: "load" }
  | { type: "ready"; total: number }
  | { type: "error"; message: string };

function docReducer(_: DocState, action: DocAction): DocState {
  switch (action.type) {
    case "load": return { phase: "loading" };
    case "ready": return { phase: "ready", total: action.total };
    case "error": return { phase: "error", message: action.message };
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

export function PdfViewer({ bookId, initialPage = 1, onPageChange, isBookmarked, onAddBookmark }: Props) {
  const canvas1Ref = useRef<HTMLCanvasElement | null>(null);
  const canvas2Ref = useRef<HTMLCanvasElement | null>(null);
  const docRef = useRef<PDFDocumentProxy | null>(null);
  const [page, setPage] = useState(initialPage);
  const [doc, dispatch] = useReducer(docReducer, { phase: "loading" });
  const [layout, setLayout] = useState<Layout>("single");
  const [fullscreen, setFullscreen] = useState(false);
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
    dispatch({ type: "load" });
    const task = getDocument({ url: bookFileUrl(bookId) });
    task.promise
      .then((pdf) => {
        if (cancelled) { pdf.destroy(); return; }
        docRef.current = pdf;
        dispatch({ type: "ready", total: pdf.numPages });
      })
      .catch((err) => {
        if (!cancelled) dispatch({ type: "error", message: (err as Error).message });
      });
    return () => {
      cancelled = true;
      void docRef.current?.destroy();
      docRef.current = null;
    };
  }, [bookId]);

  // Render pages — uses containerWidth from ResizeObserver for accurate sizing
  useEffect(() => {
    let cancelled = false;
    const activeTasks: Array<{ cancel: () => void }> = [];

    const pdf = docRef.current;
    const canvas1 = canvas1Ref.current;
    if (!pdf || !canvas1 || total === 0 || containerSize.w === 0) return;

    const pageWidth = layout === "double" ? Math.floor(containerSize.w / 2) - 8 : containerSize.w;
    const target = Math.min(Math.max(1, page), total);

    const dpr = window.devicePixelRatio || 1;

    const renderPage = (pageNo: number, canvas: HTMLCanvasElement) =>
      pdf.getPage(pageNo).then((p) => {
        if (cancelled) return;
        const base = p.getViewport({ scale: 1 });
        // Cover: scale to fill both dimensions, clip horizontal overflow
        const scaleW = pageWidth / base.width;
        const scaleH = containerSize.h > 0 ? containerSize.h / base.height : scaleW;
        const scale = Math.max(scaleW, scaleH) * 0.98 * dpr;
        const vp = p.getViewport({ scale });
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        canvas.width = vp.width;
        canvas.height = vp.height;
        canvas.style.width = `${vp.width / dpr}px`;
        canvas.style.height = `${vp.height / dpr}px`;
        const task = p.render({ canvasContext: ctx, canvas, viewport: vp });
        activeTasks.push(task);
        task.promise.catch(() => {});
      });

    void renderPage(target, canvas1);

    const canvas2 = canvas2Ref.current;
    if (layout === "double" && canvas2 && target + 1 <= total) {
      void renderPage(target + 1, canvas2);
    } else if (canvas2) {
      canvas2.width = 0;
      canvas2.height = 0;
    }

    return () => {
      cancelled = true;
      for (const t of activeTasks) {
        try { t.cancel(); } catch { /* ignore */ }
      }
    };
  }, [page, total, layout, containerSize]);

  // Notify parent of page changes
  useEffect(() => {
    if (total > 0) onPageChange?.(Math.min(page, total));
  }, [page, total, onPageChange]);

  // Keyboard navigation
  useEffect(() => {
    if (total === 0) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault(); goNext();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault(); goPrev();
      } else if (e.key === "Escape" && fullscreen) {
        setFullscreen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total, goNext, goPrev, fullscreen]);

  // Tap left/right edges to navigate (mobile-friendly)
  const handleCanvasAreaClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = (e.clientX - rect.left) / rect.width;
    if (relX < 0.25) goPrev();
    else if (relX > 0.75) goNext();
  }, [goPrev, goNext]);

  if (doc.phase === "error")
    return <div className={styles.error}>Failed to load: {doc.message}</div>;
  if (doc.phase === "loading")
    return <div className={styles.loading}>Loading PDF…</div>;

  const secondVisible = layout === "double" && page + 1 <= total;
  const counterLabel = secondVisible ? `${page}–${page + 1} / ${total}` : `${page} / ${total}`;

  return (
    <div className={fullscreen ? styles.wrapFull : styles.wrap}>
      <div className={styles.controls}>
        <button type="button" disabled={page <= 1} onClick={goPrev}>←</button>
        <span className={styles.counter}>{counterLabel}</span>
        <PageJump current={page} total={total} onJump={setPage} />
        <button type="button" disabled={page + step - 1 >= total} onClick={goNext}>→</button>
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
          onClick={() => setLayout((l) => l === "single" ? "double" : "single")}
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
      <div
        className={layout === "double" ? styles.canvasWrapDouble : styles.canvasWrap}
        ref={setWrapEl}
        onClick={handleCanvasAreaClick}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        <canvas ref={canvas1Ref} className={styles.canvas} />
        {layout === "double" && <canvas ref={canvas2Ref} className={styles.canvas} />}
      </div>
    </div>
  );
}
