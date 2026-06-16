import type { Schemas } from "./client";

export type BookCreateResponse = Schemas["BookCreateResponse"];

export interface UploadInput {
  file: File;
  title?: string;
  tagIds?: number[];
}

export async function uploadBook({ file, title, tagIds = [] }: UploadInput): Promise<BookCreateResponse> {
  const body = new FormData();
  body.append("file", file);
  if (title) body.append("title", title);
  for (const id of tagIds) body.append("tag_ids", String(id));

  const res = await fetch("/api/books", { method: "POST", body });
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<BookCreateResponse>;
}
