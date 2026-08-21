The app's only navigation. Swaps between the two things ScrobbleScope does.

```jsx
<ModeTabs value={mode} onChange={setMode} options={[
  {value:"album", label:"Top albums"},
  {value:"heatmap", label:"Heatmap", color:"var(--rocket-5)"}
]} />
```

Notes
- Replaces the shipped `.mode-pill` bar. The selected tab is a raised card chip on a sunken track — the same visual grammar as SegmentedControl, one size up.
- The small square is a placeholder mark, not an icon set. If real icons arrive, swap it there and nowhere else.
- The Heatmap tab's square takes `var(--rocket-5)` — the orange end of the rocket ramp — so the tab previews the data colour it leads to. Top albums stays purple.
