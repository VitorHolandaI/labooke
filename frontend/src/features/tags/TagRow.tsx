import { useState } from "react";

import type { TagOut } from "../../api/tags";
import { ConfirmDialog } from "../library/ConfirmDialog";
import { EditTagDialog } from "./EditTagDialog";
import { useDeleteTag, useUpdateTag } from "./hooks/useTagActions";
import styles from "./TagRow.module.css";

interface Props {
  tag: TagOut;
  count: number;
}

export function TagRow({ tag, count }: Props) {
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const update = useUpdateTag();
  const remove = useDeleteTag();

  return (
    <>
      <li className={styles.row}>
        <span className={styles.swatch} style={{ background: tag.color }} />
        <span className={styles.name}>{tag.name}</span>
        <span className={styles.count}>{count}</span>
        <button
          type="button"
          className={styles.actionBtn}
          onClick={() => setEditing(true)}
        >
          Edit
        </button>
        <button
          type="button"
          className={`${styles.actionBtn} ${styles.danger}`}
          onClick={() => setConfirming(true)}
        >
          Delete
        </button>
      </li>

      {editing && (
        <EditTagDialog
          tag={tag}
          isPending={update.isPending}
          errorMessage={update.error?.message}
          onClose={() => setEditing(false)}
          onSubmit={(patch) =>
            update.mutate(
              { id: tag.id, name: patch.name, color: patch.color },
              { onSuccess: () => setEditing(false) },
            )
          }
        />
      )}

      {confirming && (
        <ConfirmDialog
          title="Delete tag"
          message={`Delete "${tag.name}"? Books keep their other tags.`}
          confirmLabel="Delete"
          danger
          isPending={remove.isPending}
          onClose={() => setConfirming(false)}
          onConfirm={() =>
            remove.mutate(tag.id, { onSuccess: () => setConfirming(false) })
          }
        />
      )}
    </>
  );
}
