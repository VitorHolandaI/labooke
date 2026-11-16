import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";
import PdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

import type { PdfLoadingTask, PdfSource } from "./hooks/usePdfDocument";

GlobalWorkerOptions.workerSrc = PdfWorker;

/** Directory filled by scripts/sync-pdfjs-wasm.mjs on dev and build. */
export const PDFJS_WASM_URL = `${import.meta.env.BASE_URL}pdfjs-wasm/`;

/**
 * Open a PDF with the wasm decoders pdf.js 6 uses for JBIG2/CCITT/JPX pages.
 * Omitting wasmUrl leaves scanned books blank while text PDFs still work.
 *
 * @example usePdfDocument(bookFileUrl(id), openPdfDocument)
 */
export function openPdfDocument(source: PdfSource): PdfLoadingTask<PDFDocumentProxy> {
  return getDocument({ ...source, wasmUrl: PDFJS_WASM_URL });
}
