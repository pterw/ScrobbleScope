The 365-day listening heatmap — the one screen in ScrobbleScope that already looks right.

```jsx
<HeatmapFrame stats={[
  {label:"Scrobbles", value:"18,204"},
  {label:"Daily average", value:"49.9"},
  {label:"Best day", value:"312", sub:"14 Mar"},
  {label:"Current streak", value:"41", sub:"days"}
]}>
  <HeatmapGrid values={days} startMonth={8} />
</HeatmapFrame>
```

Notes
- Colour comes from `rocket_r` (seaborn), transcribed into `tokens/heatmap.css`. Do not substitute a green GitHub ramp or re-tint toward purple.
- The frame background is `--heatmap-surface` (#faf8f3 / #181520) with a 14px radius — the origin of the whole warm palette.
- On a phone use `HeatmapStrips` instead of `HeatmapGrid`: four stacked 13-week strips labelled by season, 1px gap. Cell size stays the same — never shrink cells below ~8px.
- `--heatmap-empty` is warm (`#e8e2d6` light / `#2a2a2a` dark) so zero-days sit on cream instead of reading as cold grey dots.
- Export is layout-independent: CSV and JPEG always render the desktop 53×7 grid, even when the user is on mobile. The UI says nothing about this.
