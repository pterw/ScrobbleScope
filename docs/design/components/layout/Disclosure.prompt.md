Progressive disclosure inside a form card. Carries the play/track minimums on the index form; label it in plain language (“What counts as listened”), never with the internal word *thresholds*.

```jsx
<Disclosure label="What counts as listened" summary="≥10 plays · ≥3 tracks" open={open} onToggle={setOpen}>
  …steppers…
</Disclosure>
```

Two rules, both non-negotiable: it expands **in place** (nothing below it jumps out of view on mobile), and the collapsed summary always states the active values.
