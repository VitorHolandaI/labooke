import { useEffect, useState } from "react";

import type { SearchMode } from "./hooks/useLibraryFilters";
import styles from "./SearchBar.module.css";

interface Props {
  q: string;
  mode: SearchMode;
  onChange: (patch: { q?: string; mode?: SearchMode }) => void;
  debounceMs?: number;
}

export function SearchBar({ q, mode, onChange, debounceMs = 250 }: Props) {
  const [draft, setDraft] = useState(q);
  const [lastQ, setLastQ] = useState(q);

  if (q !== lastQ) {
    setLastQ(q);
    setDraft(q);
  }

  useEffect(() => {
    if (draft === q) return;
    const handle = window.setTimeout(() => onChange({ q: draft }), debounceMs);
    return () => window.clearTimeout(handle);
  }, [draft, q, debounceMs, onChange]);

  return (
    <div className={styles.bar} role="search">
      <input
        type="search"
        className={styles.input}
        placeholder={mode === "semantic" ? "Search content (semantic)…" : "Search title or filename…"}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        aria-label="Library search"
      />
      <div className={styles.modeGroup} role="group" aria-label="Search mode">
        <button
          type="button"
          className={mode === "lexical" ? styles.modeActive : styles.mode}
          onClick={() => onChange({ mode: "lexical" })}
        >
          Title
        </button>
        <button
          type="button"
          className={mode === "semantic" ? styles.modeActive : styles.mode}
          onClick={() => onChange({ mode: "semantic" })}
        >
          Semantic
        </button>
      </div>
    </div>
  );
}
