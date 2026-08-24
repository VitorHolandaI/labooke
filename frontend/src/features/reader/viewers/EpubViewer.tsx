import ePub from "epubjs";
import type { Book, Rendition } from "epubjs";
import JSZip from "jszip";
import { useCallback, useEffect, useRef, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import { PageJump } from "./PageJump";
import styles from "./EpubViewer.module.css";

// The UMD build of epubjs (selected by Vite via the package "browser"
// field) resolves JSZip from the global scope — see gotchas/epub-viewer-bug.md.
(window as { JSZip?: unknown }).JSZip = JSZip;

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
        });
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

  // Keyboard navigation
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); next(); }
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); prev(); }
      else if (e.key === "Escape" && fullscreen) setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev, fullscreen]);

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
          className={fullscreen ? styles.ctrlActive : styles.ctrl}
          onClick={() => setFullscreen((f) => !f)}
          title={fullscreen ? "Sair da tela cheia (Esc)" : "Tela cheia"}
        >
          {fullscreen ? "⊠ Sair" : "⛶ Tela cheia"}
        </button>
      </div>
      {error && <div className={styles.error}>Failed to load: {error}</div>}
      <div ref={containerRef} className={styles.viewport} />
    </div>
  );
}
