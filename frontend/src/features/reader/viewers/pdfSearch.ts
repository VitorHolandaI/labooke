export interface PdfSearchPage {
  getTextContent: () => Promise<{ items: readonly unknown[] }>;
}

export interface PdfSearchDocument {
  numPages: number;
  getPage: (pageNumber: number) => Promise<PdfSearchPage>;
}

export interface PdfSearchHit {
  page: number;
  matches: number;
}

export interface PdfSearchSummary {
  hits: PdfSearchHit[];
  matches: number;
}

function textFromItem(item: unknown): string {
  if (!item || typeof item !== "object" || !("str" in item)) return "";
  return typeof item.str === "string" ? item.str : "";
}

/** Normalize extracted PDF text for case- and accent-insensitive matching. */
export function normalizePdfText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/-\s+/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLocaleLowerCase("pt-BR");
}

function countMatches(text: string, query: string): number {
  let count = 0;
  let offset = 0;
  while ((offset = text.indexOf(query, offset)) >= 0) {
    count += 1;
    offset += query.length;
  }
  return count;
}

/** Search every text-bearing page and return page-level hit counts. */
export async function searchPdfDocument(
  pdf: PdfSearchDocument,
  query: string,
  signal?: AbortSignal,
): Promise<PdfSearchSummary> {
  const needle = normalizePdfText(query);
  const hits: PdfSearchHit[] = [];
  let matches = 0;

  for (let page = 1; page <= pdf.numPages && needle; page += 1) {
    if (signal?.aborted) throw new DOMException("PDF search cancelled", "AbortError");
    const content = await (await pdf.getPage(page)).getTextContent();
    const text = normalizePdfText(content.items.map(textFromItem).join(" "));
    const pageMatches = countMatches(text, needle);
    if (pageMatches > 0) hits.push({ page, matches: pageMatches });
    matches += pageMatches;
  }

  return { hits, matches };
}
