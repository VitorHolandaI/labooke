export type ReaderLayout = "single" | "double";

// epubjs treats a minSpreadWidth of 0 as unset and falls back to 800px
// (rendition.js determineLayoutProperties), so "always" needs a truthy one.
export const EPUB_SPREAD_MIN_WIDTH = 1;

/**
 * epubjs spread setting for the reader's one/two page toggle.
 *
 * Example: `rendition.spread(epubSpread("double"), EPUB_SPREAD_MIN_WIDTH)`.
 */
export function epubSpread(layout: ReaderLayout): "none" | "always" {
  return layout === "double" ? "always" : "none";
}
