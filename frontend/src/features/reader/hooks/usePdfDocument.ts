import { useEffect, useReducer, useState } from "react";

export type PdfDocState =
  { phase: "loading" } | { phase: "ready"; total: number } | { phase: "error"; message: string };

type PdfDocAction =
  { type: "load" } | { type: "ready"; total: number } | { type: "error"; message: string };

export interface PdfSource {
  url: string;
}

/** The slice of pdfjs's PDFDocumentLoadingTask this hook needs. */
export interface PdfLoadingTask<Doc> {
  promise: Promise<Doc>;
  destroy: () => Promise<void>;
}

export type OpenPdf<Doc> = (source: PdfSource) => PdfLoadingTask<Doc>;

function pdfDocReducer(_: PdfDocState, action: PdfDocAction): PdfDocState {
  switch (action.type) {
    case "load":
      return { phase: "loading" };
    case "ready":
      return { phase: "ready", total: action.total };
    case "error":
      return { phase: "error", message: action.message };
  }
}

/**
 * Load the PDF at `url` and destroy it when the url changes or on unmount.
 * pdfjs 6 removed `PDFDocumentProxy.destroy()`; the loading task owns it now.
 *
 * @example const { pdf, state } = usePdfDocument(bookFileUrl(id), getDocument);
 */
export function usePdfDocument<Doc extends { numPages: number }>(
  url: string,
  openDocument: OpenPdf<Doc>,
) {
  const [pdf, setPdf] = useState<Doc | null>(null);
  const [state, dispatch] = useReducer(pdfDocReducer, { phase: "loading" });

  useEffect(() => {
    let cancelled = false;
    dispatch({ type: "load" });
    const task = openDocument({ url });
    task.promise
      .then((nextPdf) => {
        if (cancelled) return;
        setPdf(nextPdf);
        dispatch({ type: "ready", total: nextPdf.numPages });
      })
      .catch((err: unknown) => {
        if (!cancelled) dispatch({ type: "error", message: (err as Error).message });
      });
    return () => {
      cancelled = true;
      void task.destroy();
    };
  }, [url, openDocument]);

  return { pdf, state };
}
