Brand mark. Two pairs ship: the **full mark** with the small-caps tagline (index hero, ~92px) and the **lockup** without it (app header bar, ~38px). `tagline={false}` picks the lockup.

```jsx
<Wordmark theme={dark ? "dark" : "light"} height={92} />
<Wordmark theme={dark ? "dark" : "light"} height={38} tagline={false} />
<WordmarkLockup size={18} />
```

Notes
- Files: `scrobble_scope_{light,dark,inline}.svg` (full, viewBox 420×80) and `scrobble_scope_lockup_{light,dark,inline}.svg` (no tagline, viewBox 453×69). The `inline` variants take their ink from `currentColor` and their bars from `--bars-color`.
- The component fetches the SVG and injects it **inline** — that is deliberate. `<animate>` elements do not survive SVG asset storage in this project, so the five bars are animated by CSS `@keyframes ss-bar-pulse` in `tokens/base.css` (1.6 / 1.7 / 1.9 / 2.1 / 2.3s, offset delays, never in sync). An `<img>` holds the exact box until the markup lands, so nothing reflows. `animate={false}` freezes them.
- Letterforms and the tagline never move — only the bars.
- `WordmarkLockup` is the CSS-only fallback (serif italic + purple dot) for contexts that can't load the SVG.
