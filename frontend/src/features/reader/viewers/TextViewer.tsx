import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";

import { bookFileUrl } from "../../../api/reader";
import { useSwipeGesture } from "../hooks/useSwipeGesture";
import styles from "./TextViewer.module.css";

interface Props {
  bookId: number;
  format: "txt" | "md";
  pagePages?: number;
  onPageChange?: (page: number) => void;
  initialPage?: number;
  isBookmarked?: boolean;
  onAddBookmark?: () => void;
}

const CHARS_PER_PAGE = 3000;

function renderMarkdown(src: string): string {
  // Minimal markdown: escape HTML then upgrade headings, bold, italic, code,
  // links, and paragraphs. No remote rendering to keep the bundle tiny.
  const escaped = src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const lines = escaped.split(/\r?\n/);
  const out: string[] = [];
  let inCode = false;
  let para: string[] = [];
  const flushPara = () => {
    if (para.length) {
      out.push(`<p>${para.join(" ")}</p>`);
      para = [];
    }
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (line.startsWith("```")) {
      flushPara();
      out.push(inCode ? "</code></pre>" : "<pre><code>");
      inCode = !inCode;
      continue;
    }
    if (inCode) {
      out.push(`${raw}\n`);
      continue;
    }
    const headingMatch = /^(#{1,6})\s+(.*)$/.exec(line);
    if (headingMatch) {
      flushPara();
      const level = headingMatch[1].length;
      out.push(`<h${level}>${headingMatch[2]}</h${level}>`);
      continue;
    }
    if (!line) {
      flushPara();
      continue;
    }
    let inline = line
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
    inline = inline.replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      (_, text, url) => {
        const safe = /^https?:/i.test(url) || url.startsWith("/") || url.startsWith("#");
        return `<a href="${safe ? url : "#"}" target="_blank" rel="noopener noreferrer">${text}</a>`;
      },
    );
    para.push(inline);
  }
  flushPara();
  if (inCode) out.push("</code></pre>");
  return out.join("\n");
}

type FetchState =
  | { phase: "loading" }
  | { phase: "ready"; text: string }
  | { phase: "error"; message: string };

type FetchAction =
  | { type: "load" }
  | { type: "ready"; text: string }
  | { type: "error"; message: string };

function fetchReducer(_: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case "load": return { phase: "loading" };
    case "ready": return { phase: "ready", text: action.text };
    case "error": return { phase: "error", message: action.message };
  }
}

export function TextViewer({
  bookId,
  format,
  onPageChange,
  initialPage = 1,
  isBookmarked,
  onAddBookmark,
}: Props) {
  const [fetch_, dispatch] = useReducer(fetchReducer, { phase: "loading" });
  const [page, setPage] = useState(initialPage);
  const [fullscreen, setFullscreen] = useState(false);

  // Compute pages early so goNext/goPrev can reference totalPages
  const text = fetch_.phase === "ready" ? fetch_.text : null;
  const pages = useMemo(() => {
    if (!text) return [] as string[];
    const chunks: string[] = [];
    for (let i = 0; i < text.length; i += CHARS_PER_PAGE) {
      chunks.push(text.slice(i, i + CHARS_PER_PAGE));
    }
    return chunks.length ? chunks : [""];
  }, [text]);
  const totalPages = pages.length;

  // Keep a stable ref to totalPages so goNext has no deps and doesn't
  // cause useSwipeGesture to recreate its handlers on every page count change.
  const totalPagesRef = useRef(totalPages);
  useEffect(() => { totalPagesRef.current = totalPages; });

  const goNext = useCallback(
    () => setPage((p) => {
      const max = totalPagesRef.current;
      return max ? Math.min(max, p + 1) : p;
    }),
    [],
  );
  const goPrev = useCallback(() => setPage((p) => Math.max(1, p - 1)), []);
  const { onTouchStart, onTouchEnd } = useSwipeGesture(goNext, goPrev);

  useEffect(() => {
    let cancelled = false;
    dispatch({ type: "load" });
    fetch(bookFileUrl(bookId))
      .then((response) => {
        if (!response.ok) throw new Error(`http ${response.status}`);
        return response.text();
      })
      .then((body) => {
        if (!cancelled) dispatch({ type: "ready", text: body });
      })
      .catch((err) => {
        if (!cancelled) dispatch({ type: "error", message: (err as Error).message });
      });
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  // Keyboard navigation
  useEffect(() => {
    if (totalPages === 0) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); setPage((p) => Math.min(totalPages, p + 1)); }
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); setPage((p) => Math.max(1, p - 1)); }
      else if (e.key === "Escape" && fullscreen) setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [totalPages, fullscreen]);

  useEffect(() => {
    onPageChange?.(page);
  }, [page, onPageChange]);

  if (fetch_.phase === "error") return <div className={styles.error}>Failed to load: {fetch_.message}</div>;
  if (fetch_.phase === "loading") return <div className={styles.loading}>Loading…</div>;

  const current = pages[Math.min(page, totalPages) - 1] ?? "";
  const html = format === "md" ? renderMarkdown(current) : null;

  return (
    <div
      className={fullscreen ? styles.wrapFull : styles.wrap}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
    >
      <div className={styles.controls}>
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          ← Prev
        </button>
        <span className={styles.counter}>
          {page} / {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next →
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
      {format === "md" && html !== null ? (
        <article
          className={styles.markdown}
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ) : (
        <pre className={styles.plain}>{current}</pre>
      )}
    </div>
  );
}
