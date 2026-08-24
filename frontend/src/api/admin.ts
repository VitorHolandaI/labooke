import type { Schemas } from "./client";
import { api } from "./client";

export type ScanResultOut = Schemas["ScanResultOut"];
export type BookCreateResponse = Schemas["BookCreateResponse"];

export interface ConfigOut {
  embed_model: string;
  chunk_pages: number;
  data_dir: string;
  llm_summary_pages: number;
  llm_model: string;
  llm_enabled: boolean;
}

export interface SummarizeBatchOut {
  book_ids: number[];
}

export interface InvalidateSummariesOut {
  invalidated: number;
}

export function getConfig() {
  return api.get<ConfigOut>("/api/config");
}

export function updateConfig(patch: { llm_summary_pages?: number | null }) {
  return api.put<{ llm_summary_pages: number }>("/api/admin/config", { body: { ...patch } });
}

export function triggerScan() {
  return api.post<ScanResultOut>("/api/admin/scan");
}

export function reembedAll() {
  return api.post<BookCreateResponse[]>("/api/admin/reembed-all");
}

export function invalidateSummaries() {
  return api.post<InvalidateSummariesOut>("/api/admin/summaries/invalidate");
}

export function summarizeRandom(count: number, pages?: number) {
  return api.post<SummarizeBatchOut>("/api/admin/summaries/random", {
    body: { count, pages },
  });
}

export function summarizeBatch(bookIds: number[], pages?: number) {
  return api.post<SummarizeBatchOut>("/api/admin/summaries/batch", {
    body: { book_ids: bookIds, pages },
  });
}