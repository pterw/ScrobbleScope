A flat single-select set where all options fit on 1–2 lines. Decades are the canonical case.

```jsx
<PillGroup value={decade} onChange={setDecade} options={[
  {value:"2020s",label:"2020s"},{value:"2010s",label:"2010s"},{value:"1960s",label:"1960s",disabled:true}
]} />
```

Notes
- Selected pill = filled purple with `--accent-contrast` text. Unselected pills are transparent with a hairline border, never grey fills.
- Disabled pills stay visible at 0.4 opacity — they tell the user the decade exists but holds no scrobbles.
