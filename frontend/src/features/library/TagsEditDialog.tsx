import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { BookOut } from "../../api/books";
import { createTag, type TagOut } from "../../api/tags";
import { tagsQueryKey } from "./hooks/useTags";
import { randomTagColor } from "../tags/randomColor";
import { Modal } from "./Modal";
import styles from "./Modal.module.css";

interface Props {
  book: BookOut;
  allTags: TagOut[];
  isPending?: boolean;
  onToggle: (tag: TagOut, attached: boolean) => void;
  onClose: () => void;
}

export function TagsEditDialog({ book, allTags, isPending, onToggle, onClose }: Props) {
  const attachedIds = new Set(book.tags.map((tag) => tag.id));
  const [newName, setNewName] = useState("");
  const [query, setQuery] = useState("");
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: (name: string) =>
      createTag({ name, slug: name.toLowerCase().replace(/\s+/g, "-"), color: randomTagColor() }),
    onSuccess: (tag) => {
      void queryClient.invalidateQueries({ queryKey: tagsQueryKey });
      onToggle(tag, false);
      setNewName("");
    },
  });

  const handleCreate = () => {
    const name = newName.trim();
    if (!name) return;
    createMutation.mutate(name);
  };

  const needle = query.trim().toLowerCase();
  const visibleTags = needle
    ? allTags.filter((tag) => tag.name.toLowerCase().includes(needle))
    : allTags;

  return (
    <Modal title={`Edit tags — ${book.title}`} onClose={onClose}>
      <input
        className={styles.input}
        type="search"
        placeholder="Filter tags…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        aria-label="Filter tags"
      />
      <ul className={styles.tagList}>
        {visibleTags.length === 0 && <li style={{ color: "var(--color-text-muted)", padding: "4px" }}>No tags yet — create one below.</li>}
        {visibleTags.map((tag) => {
          const attached = attachedIds.has(tag.id);
          return (
            <li key={tag.id} className={styles.tagRow}>
              <label style={{ display: "flex", gap: "8px", alignItems: "center", flex: 1 }}>
                <input
                  type="checkbox"
                  checked={attached}
                  disabled={isPending}
                  onChange={() => onToggle(tag, attached)}
                />
                <span style={{ background: tag.color, width: 12, height: 12, borderRadius: 3 }} />
                {tag.name}
              </label>
            </li>
          );
        })}
      </ul>
      <div style={{ display: "flex", gap: "8px" }}>
        <input
          className={styles.input}
          placeholder="New tag name…"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleCreate(); }}
          disabled={createMutation.isPending}
        />
        <button
          type="button"
          className={`${styles.btn} ${styles.btnPrimary}`}
          onClick={handleCreate}
          disabled={!newName.trim() || createMutation.isPending}
        >
          Create
        </button>
      </div>
      {createMutation.isError && (
        <p className={styles.error}>{createMutation.error?.message ?? "Failed to create tag"}</p>
      )}
      <div className={styles.actions}>
        <button type="button" className={styles.btn} onClick={onClose}>
          Done
        </button>
      </div>
    </Modal>
  );
}
