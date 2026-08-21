Wraps every form control so labels, hints and help text stay consistent.

```jsx
<Field label="Listening year" hint="2002–2026" help="Only plays inside this calendar year count." htmlFor="year">
  <Input id="year" mono defaultValue="2025" />
</Field>
```

Notes
- The `hint` slot is where the old tooltip-icon content goes — lowercase mono, right-aligned on the label row.
- Never stack two help lines; if a control needs more than one sentence it belongs behind a disclosure.
