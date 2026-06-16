# 0010 — CSS Modules over Tailwind

**Status:** accepted

## Context

Pick a styling approach for ~5 screens, solo project, personal use.

## Decision

CSS Modules (`Foo.module.css` → scoped classes). Vite supports this out
of the box. No Tailwind.

## Consequences

- JSX stays readable: `className={s.card}` instead of long utility
  strings.
- Real CSS skills transfer; no Tailwind class lookup tax during diff
  review.
- Bundle size is similar to Tailwind in JIT mode at this scale, so the
  decision is purely about authoring ergonomics.
- A small set of design tokens (colors, spacing) lives in CSS variables
  defined in `src/styles/`.
