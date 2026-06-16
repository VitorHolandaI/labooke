import type { Schemas } from "./client";
import { api } from "./client";

export type TagOut = Schemas["TagOut"];
export type TagCountOut = Schemas["TagCountOut"];

export function listTags() {
  return api.get<TagCountOut[]>("/api/tags");
}

export function createTag(body: Schemas["TagCreate"]) {
  return api.post<TagOut>("/api/tags", { body });
}

export function updateTag(id: number, body: Schemas["TagUpdate"]) {
  return api.patch<TagOut>(`/api/tags/${id}`, { body });
}

export function deleteTag(id: number) {
  return api.delete<void>(`/api/tags/${id}`);
}

export function mergeTags(body: Schemas["TagMergeRequest"]) {
  return api.post<void>("/api/tags/merge", { body });
}
