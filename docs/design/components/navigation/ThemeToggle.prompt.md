Two-state theme control in mono caps. Put it top-right of the page header.

```jsx
<ThemeToggle theme={theme} onChange={setTheme} />
```

Notes
- Toggling flips the `.dark` class on the page root; every token re-resolves, including `--bars-color` for the logo and pinwheel.
- The shipped app persists the choice in localStorage via `theme.js` — keep that behaviour when implementing for real.
