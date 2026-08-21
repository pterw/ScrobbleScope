Binary on/off. The dark-mode toggle in the footer bar is the only shipped instance; reuse it for any true boolean.

```jsx
<Switch id="darkSwitch" checked={dark} onChange={setDark} label="Dark mode" />
```

Notes: the knob is always white in both themes; the track turns `--accent` when on. Don't use a Switch for a disclosure — use the Disclosure row pattern in the index form.
