Native `<select>` styled to match Input. Use when there are 4+ mutually exclusive choices; use SegmentedControl for 2–3 and PillGroup for a flat set like decades.

```jsx
<Select id="release_scope" options={[
  {value:"same", label:"Same as listening year"},
  {value:"previous", label:"Previous year"},
  {value:"decade", label:"Choose decade"},
  {value:"custom", label:"Pick specific year"},
  {value:"all", label:"All years (no filter)"}
]} />
```

Notes: the chevron is two CSS gradient triangles, not an icon font — it inherits `--text-muted` in both themes.
