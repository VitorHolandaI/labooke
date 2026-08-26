import { useMemo, useState } from "react";

import type { TagOut } from "../api/tags";
import { AskPanel } from "../features/library/AskPanel";
import { BookGrid } from "../features/library/BookGrid";
import { RecentBooks } from "../features/library/RecentBooks";
import { SearchBar } from "../features/library/SearchBar";
import { TagSidebar } from "../features/library/TagSidebar";
import { UploadDropzone } from "../features/library/UploadDropzone";
import { useBooks } from "../features/library/hooks/useBooks";
import { useLibraryFilters } from "../features/library/hooks/useLibraryFilters";
import { useSearch } from "../features/library/hooks/useSearch";
import { useTags } from "../features/library/hooks/useTags";
import styles from "./LibraryPage.module.css";

export default function LibraryPage() {
  const { filters, update, toggleTag } = useLibraryFilters();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const tagsQuery = useTags();
  const allTags = (tagsQuery.data ?? []).map((tc) => tc.tag as TagOut);

  const listFilters = useMemo(
    () => ({
      tags: filters.tags.length ? filters.tags : undefined,
      exclude: filters.exclude.length ? filters.exclude : undefined,
      tag_mode: filters.tags.length ? filters.tag_mode : undefined,
      q: filters.mode === "lexical" && filters.q.trim() ? filters.q : undefined,
    }),
    [filters],
  );

  const books = useBooks(listFilters);
  const search = useSearch(
    filters.mode === "semantic" && filters.q.trim()
      ? {
          q: filters.q,
          mode: "hybrid",
          tags: filters.tags.length ? filters.tags : undefined,
          exclude: filters.exclude.length ? filters.exclude : undefined,
          tag_mode: filters.tags.length ? filters.tag_mode : undefined,
          group_by_book: true,
        }
      : null,
  );

  const booksById = useMemo(() => {
    const list = books.data?.items ?? [];
    const map = new Map<number, (typeof list)[number]>();
    for (const book of list) map.set(book.id, book);
    return map;
  }, [books.data]);

  const semanticBooks =
    filters.mode === "semantic" && filters.q.trim() && search.data
      ? search.data.groups
          .map((group) => booksById.get(group.book_id))
          .filter((book): book is NonNullable<typeof book> => Boolean(book))
      : null;

  const displayed = semanticBooks ?? books.data?.items ?? [];
  const isLoading = books.isLoading || (filters.mode === "semantic" && search.isLoading);
  const isError = books.isError || (filters.mode === "semantic" && search.isError);

  return (
    <div className={styles.layout}>
      {sidebarOpen && (
        <div
          className={styles.sidebarOverlay}
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
      <TagSidebar
        filters={filters}
        onToggle={toggleTag}
        onTagModeChange={(mode) => update({ tag_mode: mode })}
        mobileOpen={sidebarOpen}
        onMobileClose={() => setSidebarOpen(false)}
      />
      <div className={styles.content}>
        <h1 className={styles.heading}>Library</h1>
        <button
          type="button"
          className={styles.filterToggle}
          onClick={() => setSidebarOpen(true)}
          aria-expanded={sidebarOpen}
          aria-label="Open tag filters"
        >
          ☰ Filters
          {filters.tags.length + filters.exclude.length > 0
            ? ` (${filters.tags.length + filters.exclude.length})`
            : ""}
        </button>
        <SearchBar q={filters.q} mode={filters.mode} onChange={(patch) => update(patch)} />
        <AskPanel />
        <RecentBooks />
        <UploadDropzone />
        <BookGrid books={displayed} allTags={allTags} isLoading={isLoading} isError={isError} />
      </div>
    </div>
  );
}
