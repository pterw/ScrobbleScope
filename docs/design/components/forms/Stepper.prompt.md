Small numeric control for threshold values — replaces the two `<select>` dropdowns of fixed play/track counts.

```jsx
<Stepper value={minPlays} min={1} max={50} onChange={setMinPlays} />
```

Notes: value is mono and centred; the −/+ hit area is 26×28 on desktop. On touch, wrap it so the row itself is at least 44px tall.
