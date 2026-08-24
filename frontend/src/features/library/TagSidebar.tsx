import { useState } from "react";

import { useTags } from "./hooks/useTags";
import type { LibraryFilters } from "./hooks/useLibraryFilters";
import styles from "./TagSidebar.module.css";

interface Props {
  filters: LibraryFilters;
  onToggle: (id: number, opts?: { exclude?: boolean }) => void;
  onTagModeChange: (mode: "all" | "any") => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function TagSidebar({ filters, onToggle, onTagModeChange, mobileOpen, onMobileClose }: Props) {
  const { data, isLoading, isError } = useTags();
  const [query, setQuery] = useState("");

  const sidebarClass = [
    styles.sidebar,
    mobileOpen ? styles.sidebarOpen : "",
  ].join(" ");

  if (isLoading) return <aside className={sidebarClass}>Loading tags…</aside>;
  if (isError || !data) return <aside className={sidebarClass}>Could not load tags.</aside>;

  const needle = query.trim().toLowerCase();
  const visibleTags = needle
    ? data.filter(({ tag }) => tag.name.toLowerCase().includes(needle))
    : data;

  return (
    <aside className={sidebarClass} aria-label="Tag filters">
      <header className={styles.header}>
        <h2>Tags</h2>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <div className={styles.modeGroup} role="group" aria-label="Tag filter mode">
            <button
              type="button"
              className={filters.tag_mode === "all" ? styles.modeActive : styles.mode}
              onClick={() => onTagModeChange("all")}
            >
              ALL
            </button>
            <button
              type="button"
              className={filters.tag_mode === "any" ? styles.modeActive : styles.mode}
              onClick={() => onTagModeChange("any")}
            >
              ANY
            </button>
          </div>
          {onMobileClose && (
            <button
              type="button"
              className={styles.closeMobile}
              onClick={onMobileClose}
              aria-label="Close tag filters"
            >
              ✕
            </button>
          )}
        </div>
      </header>
      <input
        type="search"
        className={styles.search}
        placeholder="Filter tags…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        aria-label="Filter tags"
      />
      <p className={styles.hint}>Click to include · Alt-click to exclude.</p>
      <ul className={styles.list}>
        {visibleTags.map(({ tag, count }) => {
          const included = filters.tags.includes(tag.id);
          const excluded = filters.exclude.includes(tag.id);
          const cls = excluded ? styles.excluded : included ? styles.included : styles.tag;
          return (
            <li key={tag.id}>
              <button
                type="button"
                className={cls}
                onClick={(event) => onToggle(tag.id, { exclude: event.altKey })}
              >
                <span className={styles.dot} style={{ background: tag.color }} />
                <span className={styles.name}>{tag.name}</span>
                <span className={styles.count}>{count}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
