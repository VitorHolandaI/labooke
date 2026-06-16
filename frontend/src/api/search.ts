import type { Schemas } from "./client";
import { api } from "./client";

export type SearchResponse = Schemas["SearchResponse"];
export type SearchGroupOut = Schemas["SearchGroupOut"];
export type SearchHitOut = Schemas["SearchHitOut"];

export interface SearchInput {
  q: string;
  mode?: "semantic" | "lexical";
  tags?: number[];
  tag_mode?: "all" | "any";
  exclude?: number[];
  k?: number;
  group_by_book?: boolean;
}

export function searchLibrary(input: SearchInput) {
  return api.get<SearchResponse>("/api/search", { query: { ...input } });
}
