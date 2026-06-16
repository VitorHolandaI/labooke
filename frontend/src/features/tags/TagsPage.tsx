import { useState } from "react";

import { useTags } from "../library/hooks/useTags";
import { CreateTagForm } from "./CreateTagForm";
import { MergeTagsDialog } from "./MergeTagsDialog";
import { TagRow } from "./TagRow";
import { useCreateTag, useMergeTags } from "./hooks/useTagActions";
import styles from "./TagsPage.module.css";

export function TagsPage() {
  const { data: tagCounts = [], isLoading, isError } = useTags();
  const create = useCreateTag();
  const merge = useMergeTags();
  const [showMerge, setShowMerge] = useState(false);

  const tags = tagCounts.map((tc) => tc.tag);

  return (
    <section className={styles.page}>
      <h1 className={styles.heading}>Tags</h1>

      <CreateTagForm
        isPending={create.isPending}
        onSubmit={(body) => create.mutate(body)}
      />

      {isLoading && <p className={styles.status}>Loading…</p>}
      {isError && <p className={styles.error}>Failed to load tags.</p>}

      {tagCounts.length === 0 && !isLoading && (
        <p className={styles.status}>No tags yet. Add one above.</p>
      )}

      <ul className={styles.list}>
        {tagCounts.map(({ tag, count }) => (
          <TagRow key={tag.id} tag={tag} count={count} />
        ))}
      </ul>

      {tags.length > 1 && (
        <button
          type="button"
          className={styles.mergeBtn}
          onClick={() => setShowMerge(true)}
        >
          Merge tags…
        </button>
      )}

      {showMerge && (
        <MergeTagsDialog
          tags={tags}
          isPending={merge.isPending}
          errorMessage={merge.error?.message}
          onClose={() => setShowMerge(false)}
          onMerge={(sourceId, targetId) =>
            merge.mutate(
              { sourceId, targetId },
              { onSuccess: () => setShowMerge(false) },
            )
          }
        />
      )}
    </section>
  );
}
