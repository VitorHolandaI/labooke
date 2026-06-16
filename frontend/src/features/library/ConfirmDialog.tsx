import { Modal } from "./Modal";
import styles from "./Modal.module.css";

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isPending?: boolean;
  danger?: boolean;
  errorMessage?: string;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isPending,
  danger,
  errorMessage,
  onConfirm,
  onClose,
}: Props) {
  return (
    <Modal title={title} onClose={onClose}>
      <p>{message}</p>
      {errorMessage && <p className={styles.error}>{errorMessage}</p>}
      <div className={styles.actions}>
        <button type="button" className={styles.btn} onClick={onClose}>
          {cancelLabel}
        </button>
        <button
          type="button"
          className={`${styles.btn} ${danger ? styles.btnDanger : styles.btnPrimary}`}
          onClick={onConfirm}
          disabled={isPending}
        >
          {isPending ? "Working…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
