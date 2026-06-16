import { useState } from "react";

import type { TagOut } from "../../api/tags";
import { Modal } from "../library/Modal";
import modalStyles from "../library/Modal.module.css";
import styles from "./MergeTagsDialog.module.css";

interface Props {
  tags: TagOut[];
  isPending?: boolean;
  errorMessage?: string;
  onMerge: (sourceId: number, targetId: number) => void;
  onClose: () => void;
}

export function MergeTagsDialog({ tags, isPending, errorMessage, onMerge, onClose }: Props) {
  const [sourceId, setSourceId] = useState<number | "">("");
  const [targetId, setTargetId] = useState<number | "">("");

  const canMerge =
    sourceId !== "" && targetId !== "" && sourceId !== targetId && !isPending;

  return (
    <Modal title="Merge tags" onClose={onClose}>
      <p className={styles.hint}>
        The source tag is deleted; its books move to the target tag.
      </p>
      <div className={styles.row}>
        <label htmlFor="merge-source" className={styles.label}>Remove</label>
        <select
          id="merge-source"
          className={styles.select}
          value={sourceId}
          onChange={(e) => setSourceId(Number(e.target.value) || "")}
        >
          <option value="">Select tag…</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id} disabled={t.id === targetId}>
              {t.name}
            </option>
          ))}
        </select>
      </div>
      <div className={styles.row}>
        <label htmlFor="merge-target" className={styles.label}>Keep</label>
        <select
          id="merge-target"
          className={styles.select}
          value={targetId}
          onChange={(e) => setTargetId(Number(e.target.value) || "")}
        >
          <option value="">Select tag…</option>
          {tags.map((t) => (
            <option key={t.id} value={t.id} disabled={t.id === sourceId}>
              {t.name}
            </option>
          ))}
        </select>
      </div>
      {errorMessage && <p className={modalStyles.danger}>{errorMessage}</p>}
      <div className={modalStyles.actions}>
        <button type="button" className={modalStyles.btn} onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className={`${modalStyles.btn} ${modalStyles.btnDanger}`}
          disabled={!canMerge}
          onClick={() => {
            if (canMerge) onMerge(sourceId as number, targetId as number);
          }}
        >
          {isPending ? "Merging…" : "Merge"}
        </button>
      </div>
    </Modal>
  );
}
