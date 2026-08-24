import { useState } from "react";

import type { Schemas } from "../../api/client";
import { randomTagColor } from "./randomColor";
import styles from "./CreateTagForm.module.css";

function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

interface Props {
  isPending?: boolean;
  onSubmit: (tag: Schemas["TagCreate"]) => void;
}

export function CreateTagForm({ isPending, onSubmit }: Props) {
  const [name, setName] = useState("");
  const [color, setColor] = useState(randomTagColor);

  const trimmed = name.trim();
  const canSubmit = trimmed.length > 0 && !isPending;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({ name: trimmed, slug: toSlug(trimmed), color });
    setName("");
    setColor(randomTagColor());
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <input
        className={styles.nameInput}
        placeholder="New tag name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        aria-label="New tag name"
      />
      <input
        type="color"
        className={styles.colorInput}
        value={color}
        onChange={(e) => setColor(e.target.value)}
        aria-label="Tag color"
        title="Tag color"
      />
      <button
        type="button"
        className={styles.shuffleBtn}
        onClick={() => setColor(randomTagColor())}
        aria-label="Random color"
        title="Random color"
      >
        Random
      </button>
      <button className={styles.btn} type="submit" disabled={!canSubmit}>
        {isPending ? "Adding…" : "Add tag"}
      </button>
    </form>
  );
}
