import { useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { TagOut } from "../../api/tags";
import { createTag } from "../../api/tags";
import { useUpload } from "./hooks/useUpload";
import { useTags } from "./hooks/useTags";
import { tagsQueryKey } from "./hooks/useTags";
import styles from "./UploadDropzone.module.css";

const ACCEPTED_EXT = [".pdf", ".epub", ".txt", ".md"];

// Palette of colors to cycle through when creating new tags inline
const TAG_COLORS = [
  "#4338ca", "#0891b2", "#16a34a", "#ca8a04",
  "#dc2626", "#9333ea", "#db2777", "#ea580c",
];

type EntryStatus = "staging" | "uploading" | "ok" | "error";

interface QueueEntry {
  key: string;
  file: File;
  status: EntryStatus;
  title: string;
  tagIds: number[];
  message?: string;
}

function stemOf(filename: string): string {
  const last = filename.lastIndexOf(".");
  return last > 0 ? filename.slice(0, last) : filename;
}

function isAccepted(file: File): boolean {
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXT.some((ext) => lower.endsWith(ext));
}

function formatMB(bytes: number): string {
  const mb = bytes / 1024 / 1024;
  return mb < 0.1 ? `${(bytes / 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
}

// ── Inline tag creator ──────────────────────────────────────────────────────

interface InlineTagCreatorProps {
  onCreated: (tag: TagOut) => void;
  onCancel: () => void;
  takenColors: string[];
}

function InlineTagCreator({ onCreated, onCancel, takenColors }: InlineTagCreatorProps) {
  const queryClient = useQueryClient();
  const nextColor = TAG_COLORS.find((c) => !takenColors.includes(c)) ?? TAG_COLORS[0];
  const [name, setName] = useState("");
  const [color, setColor] = useState(nextColor);
  const [conflict, setConflict] = useState(false);

  const create = useMutation({
    mutationFn: () => {
      const slug = name.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
      return createTag({ name: name.trim(), slug, color });
    },
    onSuccess: (tag) => {
      queryClient.invalidateQueries({ queryKey: tagsQueryKey });
      onCreated(tag);
    },
    onError: (err: Error & { status?: number }) => {
      if (err.status === 409) setConflict(true);
    },
  });

  return (
    <form
      className={styles.inlineTagForm}
      onSubmit={(e) => { e.preventDefault(); if (name.trim()) { setConflict(false); create.mutate(); } }}
    >
      <input
        autoFocus
        type="text"
        className={conflict ? styles.inlineTagInputError : styles.inlineTagInput}
        placeholder={conflict ? "Name already exists" : "Tag name"}
        value={name}
        onChange={(e) => { setName(e.target.value); setConflict(false); }}
      />
      <input
        type="color"
        className={styles.inlineTagColor}
        value={color}
        onChange={(e) => setColor(e.target.value)}
      />
      <button
        type="submit"
        className={styles.inlineTagSave}
        disabled={!name.trim() || create.isPending}
      >
        {create.isPending ? "…" : "Add"}
      </button>
      <button type="button" className={styles.inlineTagCancel} onClick={onCancel}>
        ✕
      </button>
    </form>
  );
}

// ── Staging row ─────────────────────────────────────────────────────────────

interface StagingRowProps {
  entry: QueueEntry;
  allTags: TagOut[];
  onChange: (key: string, patch: Partial<QueueEntry>) => void;
  onRemove: (key: string) => void;
}

function StagingRow({ entry, allTags, onChange, onRemove }: StagingRowProps) {
  const [creatingTag, setCreatingTag] = useState(false);
  const tagSet = new Set(entry.tagIds);

  const toggleTag = (id: number) => {
    const next = tagSet.has(id)
      ? entry.tagIds.filter((t) => t !== id)
      : [...entry.tagIds, id];
    onChange(entry.key, { tagIds: next });
  };

  const handleTagCreated = (tag: TagOut) => {
    onChange(entry.key, { tagIds: [...entry.tagIds, tag.id] });
    setCreatingTag(false);
  };

  return (
    <li className={styles.stagingEntry}>
      <div className={styles.stagingHeader}>
        <span className={styles.stagingFilename}>{entry.file.name}</span>
        <button
          type="button"
          className={styles.removeBtn}
          aria-label={`Remove ${entry.file.name}`}
          onClick={() => onRemove(entry.key)}
        >
          ✕
        </button>
      </div>
      <input
        type="text"
        className={styles.titleInput}
        value={entry.title}
        aria-label="Title"
        placeholder="Title"
        onChange={(e) => onChange(entry.key, { title: e.target.value })}
      />
      <div className={styles.stagingTags}>
        {allTags.map((tag) => (
          <button
            key={tag.id}
            type="button"
            className={tagSet.has(tag.id) ? styles.tagChipOn : styles.tagChipOff}
            style={tagSet.has(tag.id) ? { background: tag.color, borderColor: tag.color } : {}}
            onClick={() => toggleTag(tag.id)}
          >
            {tag.name}
          </button>
        ))}
        {!creatingTag && (
          <button
            type="button"
            className={styles.addTagBtn}
            onClick={() => setCreatingTag(true)}
          >
            + New tag
          </button>
        )}
      </div>
      {creatingTag && (
        <InlineTagCreator
          takenColors={allTags.map((t) => t.color)}
          onCreated={handleTagCreated}
          onCancel={() => setCreatingTag(false)}
        />
      )}
    </li>
  );
}

// ── Active entry (uploading / done / error) ──────────────────────────────────

interface ActiveEntryProps {
  entry: QueueEntry;
}

function ActiveEntry({ entry }: ActiveEntryProps) {
  const fileSize = entry.file.size;
  const uploading = entry.status === "uploading";
  const done = entry.status === "ok";
  const failed = entry.status === "error";

  // Animated percentage — eases toward 92% while uploading, jumps to 100 when done.
  const [animPct, setAnimPct] = useState(0);
  useEffect(() => {
    if (!uploading) return;
    const id = setInterval(() => {
      setAnimPct((prev) => {
        if (prev >= 92) return prev;
        const step = Math.max(1, Math.ceil((92 - prev) * 0.06));
        return Math.min(prev + step, 92);
      });
    }, 60);
    return () => clearInterval(id);
  }, [uploading]);

  const displayPct = done ? 100 : animPct;
  const displayLoaded = Math.round((displayPct / 100) * fileSize);

  let statusText: string;
  if (failed) {
    statusText = entry.message ?? "Failed";
  } else if (done) {
    statusText = `${formatMB(fileSize)} — Ingesting…`;
  } else {
    statusText = `${formatMB(displayLoaded)} / ${formatMB(fileSize)} (${displayPct}%)`;
  }

  return (
    <li className={done ? styles.entryOk : failed ? styles.entryError : styles.entry}>
      <span className={styles.name}>{entry.title || entry.file.name}</span>
      <span className={styles.statusText}>{statusText}</span>
      {(uploading || done) && (
        <div className={styles.uploadProgress}>
          <div
            className={styles.uploadProgressFill}
            style={{ width: `${displayPct}%` }}
          />
        </div>
      )}
    </li>
  );
}

// ── Main dropzone ────────────────────────────────────────────────────────────

export function UploadDropzone() {
  const upload = useUpload();
  const tags = useTags();
  const [over, setOver] = useState(false);
  const [queue, setQueue] = useState<QueueEntry[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const allTags = (tags.data ?? []).map((tc) => tc.tag as TagOut);
  const stagingEntries = queue.filter((e) => e.status === "staging");
  const activeEntries = queue.filter((e) => e.status !== "staging");

  const patch = useCallback((key: string, changes: Partial<QueueEntry>) => {
    setQueue((prev) => prev.map((e) => (e.key === key ? { ...e, ...changes } : e)));
  }, []);

  const remove = useCallback((key: string) => {
    setQueue((prev) => prev.filter((e) => e.key !== key));
  }, []);

  const handleFiles = useCallback((files: FileList | File[]) => {
    const now = Date.now();
    const entries: QueueEntry[] = Array.from(files).map((file, i) => ({
      key: `${file.name}-${now}-${i}`,
      file,
      status: isAccepted(file) ? "staging" : "error",
      title: stemOf(file.name),
      tagIds: [],
      message: isAccepted(file) ? undefined : "Unsupported file type",
    }));
    setQueue((prev) => [...prev, ...entries]);
  }, []);

  const startUploads = useCallback(() => {
    const toUpload = stagingEntries;
    setQueue((prev) =>
      prev.map((e) => (e.status === "staging" ? { ...e, status: "uploading" as const } : e)),
    );
    for (const entry of toUpload) {
      const { key, file, title, tagIds } = entry;
      upload.mutate(
        { file, title: title.trim() || undefined, tagIds },
        {
          onSuccess: () => {
            setTimeout(() => patch(key, { status: "ok" }), 800);
          },
          onError: (err) => {
            patch(key, { status: "error", message: (err as Error).message });
          },
        },
      );
    }
  }, [stagingEntries, upload, patch]);

  return (
    <section
      className={over ? styles.dropzoneOver : styles.dropzone}
      onDragOver={(event) => { event.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(event) => {
        event.preventDefault();
        setOver(false);
        handleFiles(event.dataTransfer.files);
      }}
      aria-label="Upload books"
    >
      <p className={styles.text}>Drop PDF, EPUB, TXT, or MD files here.</p>
      <button type="button" className={styles.button} onClick={() => inputRef.current?.click()}>
        Choose files
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXT.join(",")}
        className={styles.input}
        onChange={(event) => {
          if (event.target.files) handleFiles(event.target.files);
          event.target.value = "";
        }}
      />

      {stagingEntries.length > 0 && (
        <>
          <ul className={styles.stagingList}>
            {stagingEntries.map((entry) => (
              <StagingRow
                key={entry.key}
                entry={entry}
                allTags={allTags}
                onChange={patch}
                onRemove={remove}
              />
            ))}
          </ul>
          <button type="button" className={styles.uploadBtn} onClick={startUploads}>
            Upload {stagingEntries.length === 1 ? "1 file" : `${stagingEntries.length} files`}
          </button>
        </>
      )}

      {activeEntries.length > 0 && (
        <ul className={styles.queue}>
          {activeEntries.map((entry) => (
            <ActiveEntry key={entry.key} entry={entry} />
          ))}
        </ul>
      )}
    </section>
  );
}
