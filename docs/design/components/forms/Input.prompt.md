Text and number entry. On mobile keep the rendered font-size at 16px or larger to stop iOS auto-zoom.

```jsx
<Input id="username" placeholder="Last.fm username" valid />
<Input id="year" mono inputMode="numeric" defaultValue="2025" />
```

Notes
- `valid` renders the green ✓ used when a username resolves; `invalid` turns the border red. Never both.
- The field background is `--surface-page` (warm), not white — inputs read as recessed against the card.
