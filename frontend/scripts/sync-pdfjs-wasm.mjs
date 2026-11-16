// Copies the pdf.js wasm decoders into the static assets served by Vite.
//
// pdf.js 6 moved JBIG2/CCITT and JPEG 2000 image decoding to WebAssembly and
// only loads them from the `wasmUrl` directory passed to getDocument(). Without
// these files, scanned PDFs (CCITT/JBIG2 pages) render as a blank canvas while
// text-based PDFs keep working — that is why the failure is per book, not global.
import { cpSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(frontendRoot, "node_modules/pdfjs-dist/wasm");
const target = resolve(frontendRoot, "public/pdfjs-wasm");

mkdirSync(target, { recursive: true });
cpSync(source, target, { recursive: true });
console.log(`pdf.js wasm assets copied to ${target}`);
