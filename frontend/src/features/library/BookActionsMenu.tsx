import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

import styles from "./BookActionsMenu.module.css";

interface Props {
  onRename: () => void;
  onEditTags: () => void;
  onReembed: () => void;
  onDelete: () => void;
}

export function BookActionsMenu({ onRename, onEditTags, onReembed, onDelete }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function onDocClick(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  // Focus first menu item when menu opens
  useEffect(() => {
    if (!open || !menuRef.current) return;
    const first = menuRef.current.querySelector<HTMLElement>('[role="menuitem"]');
    first?.focus();
  }, [open]);

  function close() {
    setOpen(false);
    triggerRef.current?.focus();
  }

  function run(action: () => void) {
    close();
    action();
  }

  function handleMenuKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const menu = menuRef.current;
    if (!menu) return;
    const items = Array.from(menu.querySelectorAll<HTMLElement>('[role="menuitem"]'));
    const idx = items.indexOf(document.activeElement as HTMLElement);

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        items[(idx + 1) % items.length]?.focus();
        break;
      case "ArrowUp":
        e.preventDefault();
        items[(idx - 1 + items.length) % items.length]?.focus();
        break;
      case "Home":
        e.preventDefault();
        items[0]?.focus();
        break;
      case "End":
        e.preventDefault();
        items[items.length - 1]?.focus();
        break;
      case "Escape":
        e.preventDefault();
        close();
        break;
      case "Tab":
        // Close menu on Tab so focus leaves naturally
        setOpen(false);
        break;
    }
  }

  return (
    <div className={styles.wrap} ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className={styles.trigger}
        onClick={() => setOpen((v) => !v)}
        aria-label="Book actions"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        ⋯
      </button>
      {open && (
        <div
          className={styles.menu}
          role="menu"
          ref={menuRef}
          onKeyDown={handleMenuKeyDown}
        >
          <button type="button" role="menuitem" className={styles.item} onClick={() => run(onRename)}>
            Rename
          </button>
          <button type="button" role="menuitem" className={styles.item} onClick={() => run(onEditTags)}>
            Edit tags
          </button>
          <button type="button" role="menuitem" className={styles.item} onClick={() => run(onReembed)}>
            Re-embed
          </button>
          <button
            type="button"
            role="menuitem"
            className={`${styles.item} ${styles.danger}`}
            onClick={() => run(onDelete)}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}
