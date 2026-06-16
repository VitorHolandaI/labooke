import type { Schemas } from "./client";
import { api } from "./client";

export type ScanResultOut = Schemas["ScanResultOut"];
export type BookCreateResponse = Schemas["BookCreateResponse"];

export interface ConfigOut {
  embed_model: string;
  chunk_pages: number;
  data_dir: string;
}

export function getConfig() {
  return api.get<ConfigOut>("/api/config");
}

export function triggerScan() {
  return api.post<ScanResultOut>("/api/admin/scan");
}

export function reembedAll() {
  return api.post<BookCreateResponse[]>("/api/admin/reembed-all");
}
