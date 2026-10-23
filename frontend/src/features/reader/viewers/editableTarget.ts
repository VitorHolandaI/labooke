/**
 * Whether a key event comes from a field the user is typing into, where the
 * reader's single-key shortcuts must not fire.
 *
 * Example: `if (isEditableTarget(e.target)) return;`
 */
export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  // jsdom leaves isContentEditable undefined, hence the strict comparison.
  return target.matches("input, textarea, select") || target.isContentEditable === true;
}
