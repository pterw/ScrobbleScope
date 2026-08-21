Use for every clickable action; one `variant="primary"` per screen, everything else secondary or ghost.

```jsx
<Button variant="primary" size="lg" fullWidth trailing="→">Search albums</Button>
<Button>Export CSV</Button>
<Button mono size="sm">Save JPEG</Button>
```

Notes
- `primary` is solid **purple** in both themes (`--button-solid-bg`): white text on light, near-black text on dark. Solid ink was tried and read as too heavy against the cream.
- `mono` renders uppercase JetBrains Mono at 10.5px — reserved for the results export bar and utility rows.
- Hover is opacity 0.86, not a colour change. No transform, no shadow.
