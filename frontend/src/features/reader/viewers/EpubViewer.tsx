import ePub from "epubjs";
import type { Book, Rendition } from "epubjs";
import JSZip from "jszip";
import { useCallback, useEffect, useRef, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useElementSize } from "../hooks/useElementSize";
import { useReaderKeyboard } from "../hooks/useReaderKeyboard";
import { EPUB_ZOOM_KEY, useReaderZoom } from "../hooks/useReaderZoom";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import { EPUB_SPREAD_MIN_WIDTH, epubSpread, type ReaderLayout } from "./epubLayout";
import { PageJump } from "./PageJump";
import { zoomFontSize } from "./readerZoom";
import { ZoomControls } from "./ZoomControls";
import styles from "./EpubViewer.module.css";

// The UMD build of epubjs (selected by Vite via the package "browser"
// field) resolves JSZip from the global scope — see gotchas/epub-viewer-bug.md.
(window as { JSZip?: unknown }).JSZip = JSZip;

// Reflowed text keeps the old scroll offset, which can land mid-page;
// re-displaying the current location snaps back to the same spot.
function redisplayCurrent(rendition: Rendition): void {
  const cfi = rendition.location?.start.cfi;
  if (cfi) void rendition.display(cfi);
}

interface Props {
  bookId: number;
  initialPage?: number;
  onPageChange?: (page: number) => void;
  isBookmarked?: boolean;
  onAddBookmark?: () => void;
}

export function EpubViewer({ bookId, initialPage = 1, onPageChange, isBookmarked, onAddBookmark }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const bookRef = useRef<Book | null>(null);
  const renditionRef = useRef<Rendition | null>(null);
  const locationsRef = useRef<string[]>([]);
  // Ref so the book-loading effect can read the latest initialPage without
  // being in its dep array (adding it would destroy and recreate the book
  // when progress data loads late).
  const initialPageRef = useRef(initialPage);
  useEffect(() => { initialPageRef.current = initialPage; }, [initialPage]);
  const [location, setLocation] = useState(initialPage);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [layout, setLayout] = useState<ReaderLayout>("single");
  const { zoom, zoomIn, zoomOut, resetZoom } = useReaderZoom(EPUB_ZOOM_KEY);
  // Same ref trick as initialPage: the rendition is built once per book and
  // picks up the current layout and zoom when it is created.
  const layoutRef = useRef(layout);
  const zoomRef = useRef(zoom);
  const [viewportEl, setViewportEl] = useState<HTMLDivElement | null>(null);
  const viewportSize = useElementSize(viewportEl);
  const attachViewport = useCallback((el: HTMLDivElement | null) => {
    containerRef.current = el;
    setViewportEl(el);
  }, []);

  const jump = useCallback(
    (pageNo: number) => {
      const locations = locationsRef.current;
      if (!renditionRef.current || locations.length === 0) return;
      const idx = Math.max(0, Math.min(pageNo - 1, locations.length - 1));
      void renditionRef.current.display(locations[idx]);
    },
    [],
  );

  const next = useCallback(() => { renditionRef.current?.next(); }, []);
  const prev = useCallback(() => { renditionRef.current?.prev(); }, []);
  const { onTouchStart, onTouchEnd } = useSwipeGesture(next, prev);

  useEffect(() => {
    if (!containerRef.current) return;
    setError(null);
    let cancelled = false;

    // epubjs resolves internal EPUB paths (META-INF/container.xml, spine
    // documents) against the book URL's base — which the API does not
    // serve. Fetching the file as an ArrayBuffer makes epubjs open the
    // zip through JSZip, so every internal resource loads offline.
    fetch(bookFileUrl(bookId))
      .then((resp) => {
        if (!resp.ok) throw new Error(`HTTP ${resp.status} ao carregar o arquivo`);
        return resp.arrayBuffer();
      })
      .then((buffer) => {
        if (cancelled) return;
        const book = ePub(buffer);
        bookRef.current = book;
        const rendition = book.renderTo(containerRef.current!, {
          width: "100%",
          height: "100%",
          flow: "paginated",
          spread: epubSpread(layoutRef.current),
          minSpreadWidth: EPUB_SPREAD_MIN_WIDTH,
        });
        rendition.themes.fontSize(zoomFontSize(zoomRef.current));
        renditionRef.current = rendition;
        rendition.display();

        book.ready
          .then(() => book.locations.generate(1024))
          .then((locations: string[]) => {
            locationsRef.current = locations;
            setTotal(locations.length);
            const ip = initialPageRef.current;
            if (ip > 1 && locations.length > 0) {
              const idx = Math.min(ip - 1, locations.length - 1);
              rendition.display(locations[idx]);
            }
          })
          .catch((err) => setError((err as Error).message));

        rendition.on("relocated", (loc: { start: { percentage: number; index?: number } }) => {
          const totalNow = book.locations.length() || 1;
          // loc.start.index is the exact location position; percentage
          // rounding is too fuzzy for the page counter.
          const page =
            loc.start.index !== undefined
              ? loc.start.index + 1
              : Math.max(1, Math.round(loc.start.percentage * totalNow) || 1);
          setLocation(page);
        });
      })
      .catch((err) => {
        if (!cancelled) setError((err as Error).message);
      });

    return () => {
      cancelled = true;
      renditionRef.current?.destroy();
      bookRef.current?.destroy();
      renditionRef.current = null;
      bookRef.current = null;
    };
  }, [bookId]);

  // epubjs only re-measures on window resize (stage.js onResize), but
  // fullscreen and the layout toggle resize the viewport without one.
  useEffect(() => {
    if (viewportSize.w === 0 || viewportSize.h === 0) return;
    renditionRef.current?.resize(viewportSize.w, viewportSize.h);
  }, [viewportSize]);

  useEffect(() => {
    layoutRef.current = layout;
    const rendition = renditionRef.current;
    if (!rendition) return;
    rendition.spread(epubSpread(layout), EPUB_SPREAD_MIN_WIDTH);
    redisplayCurrent(rendition);
  }, [layout]);

  useEffect(() => {
    zoomRef.current = zoom;
    const rendition = renditionRef.current;
    if (!rendition) return;
    rendition.themes.fontSize(zoomFontSize(zoom));
    redisplayCurrent(rendition);
  }, [zoom]);

  const exitFullscreen = useCallback(() => setFullscreen(false), []);
  useReaderKeyboard({ next, prev, exitFullscreen, zoomIn, zoomOut, resetZoom }, true);

  useEffect(() => {
    if (total > 0) onPageChange?.(location);
  }, [location, total, onPageChange]);

  return (
    <div
      className={fullscreen ? styles.wrapFull : styles.wrap}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
    >
      <div className={styles.controls}>
        <button type="button" onClick={prev}>← Prev</button>
        <span className={styles.counter}>
          {total > 0 ? `${location} / ${total}` : "…"}
        </span>
        <PageJump current={location} total={total} onJump={jump} />
        <button type="button" onClick={next}>Next →</button>
        <div className={styles.controlsSep} />
        <ZoomControls
          zoom={zoom}
          resetTitle="Fonte padrão"
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
            {isBookmarked ? "★ Marcado" : "☆ Marcar"}
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
          {fullscreen ? "⊠ Sair" : "⛶ Tela cheia"}
        </button>
      </div>
      {error && <div className={styles.error}>Failed to load: {error}</div>}
      <div
        ref={attachViewport}
        className={layout === "double" ? styles.viewport : styles.viewportSingle}
      />
    </div>
  );
}
