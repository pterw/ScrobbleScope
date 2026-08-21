The unmatched report's building block — the page that answers "why isn't my album here?".

```jsx
<UnmatchedGroup
  reason="Below your play threshold"
  count={23}
  explanation="Played, but under ≥10 plays or ≥3 unique tracks."
  fix="Lower to ≥5 plays to include 14 of these"
  items={[{album:"Hex", artist:"Bar Italia", note:"7 plays / 2 tracks"}]}
/>
```

Notes
- The count is a serif purple numeral — the same treatment as StatBlock values.
- `fix` must be actionable and specific. "Loosen your filters" is not a fix; "Lower to ≥5 plays to include 14 of these" is.
- Backend caveat: the shipped `_get_user_friendly_reason()` returns a per-album sentence, so real grouping needs a reason **code** first.
