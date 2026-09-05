# Reconciliation: the design handoff against this repository

`README.md` in this directory is the canonical design spec. It is a verbatim
snapshot and states some things this repository has deliberately overridden.
This file is the override list. Read both.

Written by Claude on 2026-08-21, in the commit that imported the tree.

---

## 1. Precedence

1. **`README.md`** -- canonical. The most recent iteration of the front-end
   work and the summary of the whole design system.
2. **`reference/design-system-readme.md`** -- the design system's own broader
   reference. Subordinate.
3. **`reference/audit-review.md`** -- a second-pass critique. Subordinate, and
   **still live.** The README is the default where the two disagree, but it
   does not automatically retire an audit finding. See `F-B21-4`.

The owner-approved overrides currently recorded are:

| Point | README says | This repo does | Why |
| --- | --- | --- | --- |
| Theme marker | `.dark` class on `<html>` | `data-theme="dark"` on `<html>` | Section 5, below |
| Wide index composition | `1.1fr 1fr`, form capped at 380px | Current source declares `3fr 5fr`; hero and form use `1.075` times the width ratio, limited by available height and capped at `2.15`. The form base cap remains `23.75rem` through Task 2. Explicit CSS dimensions own scaling; `static/css/index.css` owns measured natural heights and lower bounds. | The active remediation plan is the acceptance source. Both engines run realistic window profiles; the old 1080px denominator was an engine-independent defect. Remaining base-layout changes belong to Task 3. |
| Small label size | 11.5px | 12px | Owner review readability floor; touch and mobile sizing remain unchanged |
| Light muted text | `#6f6a7a` | `#6c6676` | Keeps small muted copy at 4.5:1 or better on every shipped light surface |
| Lockup viewBox | `0 0 453 69` | `0 0 453 74` | Section 10, below |
| Type and spacing units | px | equivalent rem at the default root size | Section 11, below |
| Header pills | Prototype scaffolding, do not build | Production navigation: Home, Heatmap, Results, Unmatched | Owner decision, `624ebb9` |
| Loading progress signal | A progress bar | One slim determinate hairline; the pinwheel is status motion only | Owner decision, `17ca9eb`; the "exactly one progress signal" rule is preserved, the hairline is that signal |
| Heatmap H1 copy | "A year of listening, *one grid.*" | "Your last 365 days, *one grid.*" | Owner copy change, `17ca9eb` |
| Heatmap mode card copy | "The heatmap always covers the last 365 days. No other settings." | "Your listening heatmap covers the last 365 days." | Owner copy change, `17ca9eb` |
| Release filter label | "Album release filter" | "Release filter" | Owner review, WP-4 |
| Run lifetime | Not specified | In-memory runs expire after two idle hours; clean routes recover the latest run from browser-session pointers | WP-4 |
| Form help affordance | `?` in a circle for tooltips | No `?` control where label and inline copy already explain; a data tooltip stays valid on a heatmap cell | Owner review, `17ca9eb` |

Unruled implementation drift is a defect, not an implicit addition to this
table.

---

## 2. What this tree is, and is not

- A **reference snapshot**. It records what the design system said on
  2026-08-21.
- **Never compiled -- but only since `F-B21-8`.** The `@source` directives in
  `static/css/tailwind.src.css` name `templates/` and `static/js/`, and an
  earlier version of this file claimed that meant nothing here is scanned.
  That was wrong. `@source` *adds* to Tailwind's automatic detection rather
  than replacing it, so the whole repository was being walked and this tree
  did reach the compiled stylesheet. The import made it visible: the drift
  gate went red on PR #173. The source line now carries `source(none)`, which
  turns automatic detection off and makes the two `@source` directives the
  entire scan. The claim is true now because the config was fixed, not
  because it was ever safe to assume. Do not restate it without checking the
  source line.
- **Not shipping code.** The `.d.ts` files are prop contracts, read as specs
  for Jinja macros. This app is server-rendered Flask and does not become React.
- **Not the owner of any live value.** See the next section.

- **A subset.** The source project holds **207 files**. 61 are imported here.
  The rest are reachable through the design MCP and are not lost.

To refresh it, or to reach anything not imported, read the Claude Design
project `7d95e96a-613b-4017-9dd7-8b74d2db9535` through the `DesignSync` tool
(`list_files`, then `get_file`). The imported files are verbatim, so a diff
against a fresh read is meaningful.

### What was left behind, and why

| Not imported | Count | Why |
| --- | --- | --- |
| `*.jsx` component implementations | 30 | React prototypes. The spec half of each component -- `.prompt.md` and `.d.ts` -- is imported. This app does not become React. |
| `*.card.html` preview cards | 25 | Design System pane furniture. They render specimens; they specify nothing. |
| `uploads/` | 50 | The source UI audits and pasted screenshots the system was built from. Superseded by `README.md`, which summarises them. |
| `guidelines/*.html` specimens | 20 | Rendered swatch and type pages. `type-candidates.html` is the one worth opening by hand when the type decision is revisited. |
| `assets/` | 16 | Binaries and SVGs. `.dockerignore` does not exclude `docs/`, so they would ship into the production image, and `README.md` says to take the wordmark and pinwheel from GitHub raw `templates/inline/`, which this repo already has. |
| `ui_kits/scrobblescope-web/` | 11 | The click-through prototype. Worth opening in a browser; not worth tracking as Flask-repo source. |
| `templates/app-page/` | 5 | Claude Design canvas scaffolding, not ScrobbleScope templates. |
| Root tooling files | 7 | `SKILL.md`, `github.md`, `_ds_bundle.js`, `_ds_manifest.json`, `_adherence.oxlintrc.json`, `thumbnail.html`, and the audit-review HTML. |
| `guidelines/*.prompt.md` | 4 | See below -- they are not what the name suggests. |

**`.prompt.md` means two different things in this project.** Under
`components/` it is a component usage spec, and all 24 are imported. Under
`guidelines/` it is the owner's authoring prompt to the design tool. Three of
the four are conversational instructions, not specification:
`brand-marks.prompt.md` reads "Your favicon.svg is botched",
`colors-status.prompt.md` asks "Where are these used and how often and why?",
and `brand-wordmark.prompt.md` is a note about crowding. They are working
history, not a contract. Do not import them as though they were specs.

The fourth, `guidelines/colors-rocket.prompt.md`, is a real specification --
and it is stale. See section 7.

---

## 3. Who owns which fact

`docs/AGENT_DOC_MAP.md` sets the rule: each fact has one owner, and every other
document links to it. This tree is a copy, so it owns nothing. When a value
here disagrees with the owner, the owner wins.

| Fact | Owner | Snapshot agrees? |
| --- | --- | --- |
| Theme colours, light and dark | the two `@plugin "daisyui-theme.mjs"` blocks in `static/css/tailwind.src.css` | Partly -- see below |
| `rocket_r` seven stops | `static/js/heatmap.js:14-22` | Yes, exactly |
| Spacing ladder | the `--spacing-*` steps in the `@theme` block | Yes |
| Radius scale | the `--radius-*` steps in the `@theme` block | Partly -- see section 6 |
| Type families | the `--font-*` steps in the `@theme` block of `static/css/tailwind.src.css`, and the kit link in `templates/base.html` | Yes -- adopted 2026-08-22, landed by WP-2 |
| Theme marker | the WP-2 deliverables list in `BATCH21_DEFINITION.md` | No -- see section 5 |
| Heatmap cell geometry | `static/js/heatmap.js:25-26` | No -- see section 7 |

**The colour agreement covers the anchors only.** An earlier version of this
file claimed every hex in the README's two colour tables matches the shipped
theme. That is false, and the PR #173 review caught it. What actually holds:

| README token | Light | Dark | In the theme? |
| --- | --- | --- | --- |
| `--surface-page` | `#faf8f3` | `#0e0c12` | Yes -- `--color-base-100` |
| `--text-strong` | `#1a1820` | `#f1ede4` | Yes -- `--color-base-content` |
| `--accent` | `#6a4baf` | `#b39dde` | Yes -- `--color-primary` |
| `--surface-sunken` | `#f0ebe0` | `#1a1622` | Yes -- `--ss-surface-sunken` |
| `--surface-card` | `#ffffff` | `#181520` | Yes -- `--ss-surface-card` |
| `--accent-contrast` | `#ffffff` | `#0e0c12` | Dark only. Light `--color-primary-content` is `#faf8f3` |
| `--text-body`, `--text-muted`, `--border-default`, `--accent-soft` | -- | -- | Yes -- the `--ss-*` theme tokens |

The status migration is partial. `--ss-good` and `--ss-bad` now carry the
README values; `--ss-warn` has no consumer and has not landed. daisyUI's
generic `--color-success`, `--color-warning` and `--color-error` slots still
carry Bootstrap's `#198754`, `#ffc107` and `#dc3545`, so page components use
the `--ss-*` tokens for the states the design specifies.

None of this is a contradiction to resolve. daisyUI's semantic slots have no
home for a body-text, muted-text, border or accent-tint colour, so those
tokens land when the WP that needs them adds them. It is recorded here so no
later agent reads "exact" and skips the comparison. **Check the theme block
before asserting parity for any token.**

---

## 4. Owner decisions, 2026-08-21

1. ~~**Type stack: self-hosted.**~~ **Reversed on 2026-08-22. Adobe Fonts
   wins.** The owner re-read the design contract and ruled that kit
   `rwy8ghw` is adopted, calling it critical. `base.html` gets the
   `use.typekit.net` link and decision 4 in `BATCH21_DEFINITION.md` was
   rewritten to match. The repo no longer overrides the canonical README
   on type, so the override table above lost its `Type families` row.
   Nothing is self-hosted and no `static/fonts/` directory is created.
2. **Design authority:** `README.md` is the default over both files in
   `reference/`. It does not always outrank an audit finding.
   `BATCH21_DEFINITION.md` is not amended.
3. **Import scope:** curated and tracked, text only.
4. **Session scope:** import only. That commit changed no code.

### The type mapping

The repo takes the README families unchanged. The table below is now a
role map, not a list of substitutions. Weights come from the verified kit
list in the `tokens/fonts.css` header.

| Token | Family | Role | Weights the kit serves |
| --- | --- | --- | --- |
| `--font-sans` | akzidenz-grotesk-next-pro | UI chrome, labels, body | 300 / 400 / 700 |
| `--font-serif` | instrument-serif | display words, 22px+ | 400 + italic |
| `--font-figure` | gotham | display numbers, 18px+ | 400 / 700; Book only |
| `--font-mono` | input-mono | form inputs, tabular numbers | 400 / 700 |
| `--font-mono-narrow` | input-mono-narrow | letterspaced caps, 9-11px | 400 / 700 |

Use `akzidenz-grotesk-next-pro`, not `akzidenz-grotesk-next`. The plain
family ships 200 roman and 800 italic and no 400, so it cannot set UI text.

Two consequences of the reversal, both easy to miss:

- **The clipping risk is resolved.** The README calls Input Mono Narrow "the
  single most likely regression": a full-width face at 9-11px letterspaced
  pushes a `nowrap` field hint into its label and clips it. The kit ships
  `input-mono-narrow`, so the repo now has the face the README asks for and
  WP-3 does not have to design around its absence. The earlier version of
  this file said the opposite, because the self-hosted plan had no narrow
  mono to offer.
- **The no-500/600 rule is technical here, not only a design rule.** Nothing
  in the kit ships a 500 or a 600, so `font-medium` and `font-semibold` can
  only synthesize fakes. `--font-weight-medium` and `--font-weight-semibold`
  are therefore deleted from the `@theme` block rather than kept. The earlier
  version kept them because Geist ships real ones; that reasoning died with
  the reversal. The design intent is unchanged: hierarchy comes from size,
  colour and letterspacing.

**The bundle contradicts itself on type, and the kit wins.** `Button.prompt.md`,
`Button.d.ts` and `Input.d.ts` all say "JetBrains Mono", not Input Mono, while
`tokens/` and the two README files carry the Adobe stack. Read those three
component files as stale on type only; the rest of what they specify stands.
The `tokens/fonts.css` header is the strongest evidence in the bundle -- it
lists every family in the kit with the weights each actually serves.

---

## 5. Theme marker: `data-theme="dark"` on `<html>`

Three mechanisms disagreed:

- Live code sets `body.dark-mode` (`static/js/theme.js:12,17`).
- The WP-2 contract says `theme.js` dual-writes `data-theme` (the WP-2
  deliverables list in `BATCH21_DEFINITION.md`).
- `README.md` says `.dark` on `<html>` (known constraint 4).

**`data-theme="dark"` on `<html>` satisfies all three.** daisyUI keys on
`data-theme`. the `@custom-variant dark` line already redefines Tailwind's `dark:`
variant against `[data-theme="dark"]`, so `dark:` utilities keep working. And
the README's real requirement is only that the marker sit on `<html>`, so the
page shell flips with the content. `templates/base.html:2` is the line.

Porting note for WP-2: `tokens/colors.css`, `tokens/elevation.css` and
`tokens/heatmap.css` all scope their dark values under `.dark`. Rewrite that
selector to `[data-theme="dark"]` when the values move into the theme.

---

## 6. Radius

`README.md` uses five steps: 4px cover art and tiny tags, 8px inputs and small
buttons, 10px stat strips and submit buttons, 14px cards and the heatmap frame,
999px pills. The `--radius-*` steps in the `@theme` block now ship all five;
WP-3 added 4px and 10px when the index and absorbed heatmap first needed them.

---

## 7. Where the bundle disagrees with itself

Found while importing. Recorded so no later agent has to re-derive them. In
every case `README.md` wins, per precedence.

| Point | `README.md` | Elsewhere in the bundle | Verdict |
| --- | --- | --- | --- |
| Dark `--heatmap-empty` | `#262230` | `#2a2a2a` in `components/heatmap/HeatmapFrame.prompt.md` | `#262230`. `tokens/heatmap.css` agrees with the README. |
| Results max width | 1180px | `--content-max: 1040px` in `tokens/spacing.css` | 1180px results, 1040px heatmap. The token is the heatmap value. |
| Form column cap | 380px | `--form-max: 460px` in `tokens/spacing.css` | 380px, per the index screen spec. |
| Figures | Gotham; "the serif gets the words, Gotham gets the numbers" | "serif number" in `StatBlock.prompt.md` and `.d.ts` | Figure face, not serif. That is `--font-figure`, which is `gotham`. |
| Heatmap cell geometry | cell radius 2px, gap 2px desktop | 11px cell in `HeatmapFrame.d.ts` | Neither matches the shipped `heatmap.js:25-26` (14px cell, 3px gap). WP-6 decides and records it. |
| `--heatmap-empty` again | `#e8e2d6` / `#262230` | `#e0e0e0` / `#2a2a2a` in `guidelines/colors-rocket.prompt.md`, **not imported** | The README values. `#e0e0e0` is the old shipped grey the design deliberately warmed away from, so that file predates the revision. It is the third variant of this one token; `tokens/heatmap.css` and the README agree and win. |

Two places where the bundle's component layer agrees with
`reference/audit-review.md` rather than with `README.md`. Both are worth
knowing before `F-B21-4` is judged:

- **Mobile input size.** `components/forms/Input.prompt.md` opens with "On
  mobile keep the rendered font-size at 16px or larger to stop iOS auto-zoom."
  That matches the shipped override at `static/css/index.css:158`. There is no
  conflict to resolve here -- the README's 13/11/10/9.5px mono sizes are
  desktop values, and the canonical bundle itself mandates 16px on mobile.
- **Loading signals.** `components/feedback/ProgressBar.d.ts` says of `value`:
  "Only show it when the value is real; otherwise show the pinwheel alone."
  That is `audit-review.md` item 7's position, stated inside the canonical
  bundle. WP-4 should read it before deciding.

---

## 8. Character set

The files in this tree are exempt from the ASCII-only rule in `AGENTS.md`
("Markdown Authoring Rules").

The design mandates specific glyphs -- the README's content rules require the
`>=` glyph over the words "at least", and the iconography section makes Unicode
characters the icon system. Transliterating them would corrupt the spec. A
verbatim snapshot also has to stay byte-comparable against a re-import.

No gate enforces ASCII; the rule is an authoring convention. Every hook is
skipped here anyway, because `.pre-commit-config.yaml:2` excludes `docs/`.

This file, being Claude's prose rather than a snapshot, follows the rule.

---

## 9. Related findings

- **`F-B21-2`** -- the three dormant Tailwind seams WP-2 closes. Section 5
  above settles the theme-marker seam.
- **`F-B21-4`** -- the four screens where `reference/audit-review.md` dissents
  from `README.md`. Open; judged per WP.
- **`F-B21-5`** -- accessibility and mobile defects the handoff does not
  resolve.

---

## 10. The lockup asset, 2026-08-24

Section numbers are never reused here and never renumbered, so this is
appended rather than slotted next to the asset material in section 7. Other
documents cite these sections by number.

`templates/inline/scrobble_scope_lockup_inline.svg` was not imported with the
handoff -- assets were excluded, per section 2 -- so WP-2 derived one by
removing the tagline group from the full mark and tightening the viewBox. The
letterforms were left where they sat. In the full mark the bars descend
alongside the tagline, which balances them; with the tagline gone they hung
about 13 units below the text baseline. The owner reported it on 2026-08-24.

The design project does hold a canonical lockup at
`assets/scrobble_scope_lockup_inline.svg`. Two of its three differences are
now adopted:

1. **`#logo-text` carries a static transform**,
   `translate(99.10, 39.40) scale(1.1) translate(-99.10, -29.21)`. It scales
   the word 1.1x and seats its baseline on the bars'. It is an attribute, not
   an animation -- the letterforms still never move.
2. **Every bar ends at exactly 63.50**, the baseline `README.md` "Wordmark
   animation" names. The repo's bars ended between 63.46 and 63.70, so the
   `transform-origin: 0 63.5px` in `static/css/shell.css` was slightly wrong
   for each of the five.

**The viewBox is the deviation. The repo wins here.** Canonical is
`0 0 453 69`, which cuts 3.2 user units off the `p` descender in "Scope" --
measured in Chromium, not inferred. The repo uses `0 0 453 74`, which is the
same frame with enough height to keep the descender whole. The owner ruled
this on 2026-08-24 after seeing both rendered.

Three tests in `tests/test_template_shell.py` hold all three facts, because
none of them is visible to any other gate: a clipped descender renders as a
slightly odd letter, and a drifting bar foot renders as nothing at all.

The full mark, `scrobble_scope_inline.svg`, is unaffected and was not
touched. Its tagline still balances the bars.

---

## 11. Units: rem for type and space, 2026-08-24

**The snapshot states px. The repo states rem. The repo wins, and this is
the record of that.**

`tokens/typography.css` gives the type ladder as `--text-display-lg: 42px`
down to `--text-label: 11.5px`. `tokens/spacing.css` gives a 4px ladder and
says outright that it replaces "the current Bootstrap build mixes
0.25/0.35/0.45/0.6rem values". So the snapshot moved deliberately from rem to
px, and this repository moved back.

**It moved back before anyone noticed.** WP-1 wrote the type scale into
`static/css/tailwind.src.css` in rem -- `--text-body: 1rem`,
`--text-label: 0.8125rem` -- because that is Tailwind v4's own convention for
the `--text-*` namespace. The px figures in the snapshot and the rem figures
in the repo are the same sizes at a 16px root, so nothing looked wrong and
nothing recorded the divergence. WP-3 then wrote page spacing in px against a
type scale already in rem.

**The owner ruled on 2026-08-24:** rem for font size and spacing, px for thin
details a reader never scales. `AGENTS.md` "UI and Accessibility Rules" item 1
carries the rule for every agent; this section carries why it overrides the
snapshot. It was written as item 6 of "Proposal and Design Rules" and moved
the same day, and this pointer was left behind -- the same class of defect
this section documents, in the sentence that documents it.

The reason is not only preference. A reader who raises the browser font size
gets larger text inside boxes that did not grow, so the text crowds and
clips -- and that mismatch is worse than either unit used consistently,
because the type scale was already rem. WCAG technique C14 makes relative
font sizes a sufficient technique for 1.4.4 Resize Text. The spacing half is
this repository's choice, made for the same reason, and it is not a WCAG
requirement -- do not cite it as one.

**Read the snapshot's px figures as sizes, not as units.** 42px means
2.625rem. The design's own values are unchanged by this; only how they are
written down is.

The WP-3 sweep converted 102 declarations in `static/css/index.css`,
`static/css/heatmap.css` and `static/css/shell.css`, proved neutral by measuring
1917 rendered values across three viewports and three page states. Two custom
properties escaped that sweep: the desktop and mobile header heights still
held text in px. PR review converted them to equivalent rem values and added a
browser check that raises the root font size and measures the rendered header.

`shell.css` is in that list because it loads on every page, migrated or not,
so leaving it in px put px spacing around rem type on the one page already
converted. That is the mismatch this section exists to prevent, and it would
have sat there until WP-8.

`global.css`, `loading.css`, `results.css` and `unmatched.css` are not
converted. Each is a Bootstrap-era page stylesheet that its own work package
rewrites -- WP-4, WP-5, WP-7 -- so converting them now would churn a file
about to be replaced, for pages whose type is not rem yet either. Convert
each one with the rewrite that owns it. `error.css` keeps px in the rules
WP-2 wrote; only its touch-target rule moved, with the rule that changed it.
