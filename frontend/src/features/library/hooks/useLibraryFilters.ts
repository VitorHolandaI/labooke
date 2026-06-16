import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export type SearchMode = "lexical" | "semantic";

export interface LibraryFilters {
  q: string;
  mode: SearchMode;
  tags: number[];
  exclude: number[];
  tag_mode: "all" | "any";
}

function parseIds(value: string | null): number[] {
  if (!value) return [];
  return value
    .split(",")
    .map((part) => Number.parseInt(part, 10))
    .filter((n) => Number.isFinite(n) && n > 0);
}

function serializeIds(ids: number[]): string | null {
  return ids.length ? ids.join(",") : null;
}

export function useLibraryFilters() {
  const [params, setParams] = useSearchParams();

  const filters = useMemo<LibraryFilters>(
    () => ({
      q: params.get("q") ?? "",
      mode: (params.get("mode") as SearchMode | null) === "semantic" ? "semantic" : "lexical",
      tags: parseIds(params.get("tags")),
      exclude: parseIds(params.get("exclude")),
      tag_mode: params.get("tag_mode") === "any" ? "any" : "all",
    }),
    [params],
  );

  const update = useCallback(
    (patch: Partial<LibraryFilters>) => {
      setParams((current) => {
        const next = new URLSearchParams(current);
        const setOrDelete = (key: string, value: string | null) => {
          if (value === null || value === "") next.delete(key);
          else next.set(key, value);
        };
        if ("q" in patch) setOrDelete("q", patch.q ?? null);
        if ("mode" in patch) setOrDelete("mode", patch.mode === "semantic" ? "semantic" : null);
        if ("tags" in patch) setOrDelete("tags", serializeIds(patch.tags ?? []));
        if ("exclude" in patch) setOrDelete("exclude", serializeIds(patch.exclude ?? []));
        if ("tag_mode" in patch)
          setOrDelete("tag_mode", patch.tag_mode === "any" ? "any" : null);
        return next;
      });
    },
    [setParams],
  );

  const toggleTag = useCallback(
    (id: number, opts: { exclude?: boolean } = {}) => {
      const list = opts.exclude ? filters.exclude : filters.tags;
      const other = opts.exclude ? filters.tags : filters.exclude;
      const isOn = list.includes(id);
      const nextList = isOn ? list.filter((t) => t !== id) : [...list, id];
      const nextOther = other.filter((t) => t !== id);
      update(
        opts.exclude
          ? { exclude: nextList, tags: nextOther }
          : { tags: nextList, exclude: nextOther },
      );
    },
    [filters.exclude, filters.tags, update],
  );

  return { filters, update, toggleTag };
}
