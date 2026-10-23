import { useCallback, useState } from "react";

export interface BookSelection {
  selected: ReadonlySet<number>;
  toggle: (id: number) => void;
  selectIds: (ids: readonly number[]) => void;
  addIds: (ids: readonly number[]) => void;
  clear: () => void;
}

/**
 * Checkbox state for one admin book list; each list keeps its own.
 *
 * Example: `const selection = useBookSelection(); selection.toggle(book.id);`
 */
export function useBookSelection(): BookSelection {
  const [selected, setSelected] = useState<ReadonlySet<number>>(new Set());

  const toggle = useCallback((id: number) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);
  const selectIds = useCallback((ids: readonly number[]) => setSelected(new Set(ids)), []);
  const addIds = useCallback(
    (ids: readonly number[]) => setSelected((current) => new Set([...current, ...ids])),
    [],
  );
  const clear = useCallback(() => setSelected(new Set()), []);
  return { selected, toggle, selectIds, addIds, clear };
}
