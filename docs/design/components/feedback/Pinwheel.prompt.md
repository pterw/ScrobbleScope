The one loading indicator in the product. Use it for any wait over ~1s — heatmap generation and the album scan alike.

```jsx
<Pinwheel size={132} label="Fetching scrobbles" />
```

Notes
- Blades fill from `--bars-color`, so it turns purple in light mode and lilac in dark automatically.
- The SVG must keep `overflow: visible` — blades translate 5.4 units outside the viewBox at the peak of the cycle and get clipped otherwise.
- Source of truth for the geometry and SMIL timing: `assets/scrobblescope_pinwheel.svg` (from `templates/inline/` in the app repo). Do not re-time it.
