Exclusive 2–3 option switch inside a form. Replaces the "Sort by" dropdown.

```jsx
<SegmentedControl value={sort} onChange={setSort} options={[
  {value:"playcount", label:"Play count"},
  {value:"playtime", label:"Play time"}
]} />
```

Notes: the selected segment is a raised card chip (`--surface-card` + `--shadow-chip`), the track is `--surface-page`. Max three options — past that, use Select.
