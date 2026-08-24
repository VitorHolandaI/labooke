import { useState } from "react";

import type { TagOut } from "../../api/tags";
import { Modal } from "../library/Modal";
import { randomTagColor } from "./randomColor";
import modalStyles from "../library/Modal.module.css";

interface Props {
  tag: TagOut;
  isPending?: boolean;
  errorMessage?: string;
  onSubmit: (patch: { name: string; color: string }) => void;
  onClose: () => void;
}

export function EditTagDialog({ tag, isPending, errorMessage, onSubmit, onClose }: Props) {
  const [name, setName] = useState(tag.name);
  const [color, setColor] = useState(tag.color);

  const trimmed = name.trim();
  const changed = trimmed !== tag.name || color !== tag.color;
  const canSubmit = trimmed.length > 0 && changed && !isPending;

  return (
    <Modal title="Edit tag" onClose={onClose}>
      <form
        className={modalStyles.body}
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) onSubmit({ name: trimmed, color });
        }}
      >
        <label htmlFor="edit-tag-name">Name</label>
        <input
          id="edit-tag-name"
          className={modalStyles.input}
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
        />
        <label htmlFor="edit-tag-color">Color</label>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <input
            id="edit-tag-color"
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
          />
          <button
            type="button"
            className={modalStyles.btn}
            onClick={() => setColor(randomTagColor())}
          >
            Random
          </button>
        </div>
        {errorMessage && <p className={modalStyles.danger}>{errorMessage}</p>}
        <div className={modalStyles.actions}>
          <button type="button" className={modalStyles.btn} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={`${modalStyles.btn} ${modalStyles.btnPrimary}`}
            disabled={!canSubmit}
          >
            {isPending ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
