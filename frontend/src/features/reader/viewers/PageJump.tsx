import { useState } from "react";

import styles from "./PageJump.module.css";

interface Props {
  current: number;
  total: number;
  onJump: (page: number) => void;
}

export function PageJump({ current, total, onJump }: Props) {
  const [draft, setDraft] = useState("");

  function commit() {
    const n = Number.parseInt(draft, 10);
    if (Number.isFinite(n) && n >= 1) onJump(Math.min(n, total || n));
    setDraft("");
  }

  return (
    <span className={styles.jump}>
      <input
        type="number"
        min={1}
        max={total || undefined}
        className={styles.input}
        value={draft}
        placeholder={String(current)}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
        }}
        aria-label="Ir para página"
      />
      <button type="button" className={styles.btn} onClick={commit} disabled={!draft.trim()}>
        Ir
      </button>
    </span>
  );
}