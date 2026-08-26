import { TextLayer } from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { useEffect, useRef, useState } from "react";

import { normalizePdfText } from "./pdfSearch";
import styles from "./PdfViewer.module.css";

interface Props {
  pdf: PDFDocumentProxy;
  pageNumber: number;
  availableWidth: number;
  availableHeight: number;
  query: string;
}

function highlightMatches(textLayer: TextLayer, query: string) {
  const needle = normalizePdfText(query);
  textLayer.textDivs.forEach((div, index) => {
    const text = normalizePdfText(textLayer.textContentItemsStr[index] ?? "");
    div.classList.toggle(styles.searchMatch, Boolean(needle && text.includes(needle)));
  });
}

/** Render one PDF page with aligned canvas and selectable text layers. */
export function PdfPageLayer({ pdf, pageNumber, availableWidth, availableHeight, query }: Props) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const textRef = useRef<HTMLDivElement | null>(null);
  const textLayerRef = useRef<TextLayer | null>(null);
  const [textVersion, setTextVersion] = useState(0);

  useEffect(() => {
    if (availableWidth <= 0) return;
    let cancelled = false;
    let renderTask: { cancel: () => void; promise: Promise<unknown> } | null = null;
    let textLayer: TextLayer | null = null;

    void pdf
      .getPage(pageNumber)
      .then(async (pdfPage) => {
        const shell = shellRef.current;
        const canvas = canvasRef.current;
        const text = textRef.current;
        if (cancelled || !shell || !canvas || !text) return;

        const base = pdfPage.getViewport({ scale: 1 });
        const widthScale = availableWidth / base.width;
        const heightScale = availableHeight > 0 ? availableHeight / base.height : widthScale;
        const scale = Math.max(widthScale, heightScale) * 0.98;
        const viewport = pdfPage.getViewport({ scale });
        const outputViewport = pdfPage.getViewport({
          scale: scale * (window.devicePixelRatio || 1),
        });
        shell.style.width = `${viewport.width}px`;
        shell.style.height = `${viewport.height}px`;
        text.style.setProperty("--total-scale-factor", String(scale));
        text.replaceChildren();

        const context = canvas.getContext("2d");
        if (!context) return;
        canvas.width = outputViewport.width;
        canvas.height = outputViewport.height;
        renderTask = pdfPage.render({ canvasContext: context, canvas, viewport: outputViewport });
        void renderTask.promise.catch(() => {});
        textLayer = new TextLayer({
          textContentSource: pdfPage.streamTextContent(),
          container: text,
          viewport,
        });
        textLayerRef.current = textLayer;
        await textLayer.render();
        if (!cancelled) setTextVersion((version) => version + 1);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
      renderTask?.cancel();
      textLayer?.cancel();
      textLayerRef.current = null;
    };
  }, [pdf, pageNumber, availableWidth, availableHeight]);

  useEffect(() => {
    if (textLayerRef.current) highlightMatches(textLayerRef.current, query);
  }, [query, textVersion]);

  return (
    <div className={styles.pageLayer} ref={shellRef}>
      <canvas ref={canvasRef} className={styles.canvas} />
      <div ref={textRef} className={styles.textLayer} data-pdf-text-layer="true" />
    </div>
  );
}
