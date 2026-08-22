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

Where this repository overrides `README.md`, the list is short and complete:

| Point | README says | This repo does | Why |
| --- | --- | --- | --- |
| Type families | Adobe Typekit kit `rwy8ghw`, 5 families | Self-hosted Geist / Instrument Serif / JetBrains Mono | Owner decision 1, below |
| Theme marker | `.dark` class on `<html>` | `data-theme="dark"` on `<html>` | Section 5, below |
| Radius steps | 5 values | 3 shipped, 2 still to add | Section 6, below |

Nothing else in `README.md` is overridden.

---

## 2. What this tree is, and is not

- A **reference snapshot**. It records what the design system said on
  2026-08-21.
- **Never compiled.** Tailwind's `@source` directives at
  `static/css/tailwind.src.css:3-4` cover `templates/` and `static/js/` only.
  Nothing here is scanned, and nothing here can move `static/css/tailwind.css`.
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
| Theme colours, light and dark | `static/css/tailwind.src.css:69-137` | Yes, exactly |
| `rocket_r` seven stops | `static/js/heatmap.js:14-22` | Yes, exactly |
| Spacing ladder | `static/css/tailwind.src.css:36-42` | Yes |
| Radius scale | `static/css/tailwind.src.css:45-47` | Partly -- see section 6 |
| Type families | `BATCH21_DEFINITION.md:155-158` | No -- see section 4 |
| Theme marker | `BATCH21_DEFINITION.md:190` | No -- see section 5 |
| Heatmap cell geometry | `static/js/heatmap.js:25-26` | No -- see section 7 |

The colour agreement is exact, not approximate. Every hex value in the
README's two colour tables matches the shipped theme blocks.

---

## 4. Owner decisions, 2026-08-21

1. **Type stack: self-hosted.** Decision 4 in `BATCH21_DEFINITION.md:155-158`
   stands. Kit `rwy8ghw` is not adopted. No `use.typekit.net` link goes into
   `base.html`. This is the one place the owner ruled against the canonical
   README, deliberately.
2. **Design authority:** `README.md` is the default over both files in
   `reference/`. It does not always outrank an audit finding.
   `BATCH21_DEFINITION.md` is not amended.
3. **Import scope:** curated and tracked, text only.
4. **Session scope:** import only. That commit changed no code.

### The type mapping

| README role | README family | This repo | Note |
| --- | --- | --- | --- |
| `--font-sans` chrome, body | akzidenz-grotesk-next-pro | Geist | `tailwind.src.css:9` |
| `--font-serif` words, 22px+ | instrument-serif | Instrument Serif | identical |
| `--font-figure` numbers, 18px+ | gotham Book | JetBrains Mono | no self-hosted figure face |
| `--font-mono` inputs, tabular | input-mono | JetBrains Mono | `tailwind.src.css:11` |
| `--font-mono-narrow` 9-11px caps | input-mono-narrow | JetBrains Mono | no narrow variant exists |

Two consequences, both easy to miss:

- **The clipping risk gets worse, not better.** The README calls Input Mono
  Narrow "the single most likely regression": the full-width face at 9-11px
  letterspaced pushes a `nowrap` field hint into its label and clips it. There
  is no narrow JetBrains Mono, so this repository permanently uses the
  full-width face the README warns against. **WP-3 must measure label and hint
  widths at 9-11px.** Do not assume the README's fix carried over. It did not.
- **The no-500/600 rule is a design rule here, not a technical one.** The
  README bans weights 500 and 600 because no Adobe family in the kit ships
  them, so `font-medium` synthesizes a fake. Geist does ship 300-700, so
  `--font-weight-medium: 500` and `--font-weight-semibold: 600` at
  `tailwind.src.css:15-16` are real weights. Keep the tokens. Still follow the
  design intent: hierarchy comes from size, colour and letterspacing.

**The component layer already used the self-hosted names.** `Button.prompt.md`,
`Button.d.ts` and `Input.d.ts` all say "JetBrains Mono", not Input Mono. Only
`tokens/` and the two README files carry the Adobe stack. The mapping above
therefore agrees with most of the bundle rather than fighting it.

---

## 5. Theme marker: `data-theme="dark"` on `<html>`

Three mechanisms disagreed:

- Live code sets `body.dark-mode` (`static/js/theme.js:12,17`).
- The WP-2 contract says `theme.js` dual-writes `data-theme`
  (`BATCH21_DEFINITION.md:190`).
- `README.md` says `.dark` on `<html>` (known constraint 4).

**`data-theme="dark"` on `<html>` satisfies all three.** daisyUI keys on
`data-theme`. `tailwind.src.css:139` already redefines Tailwind's `dark:`
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
999px pills. `tailwind.src.css:45-47` ships three: 8, 14, 999.

**4px and 10px are still missing.** Whichever WP first needs album cover art
(WP-5) or a stat strip (WP-4) adds them.

---

## 7. Where the bundle disagrees with itself

Found while importing. Recorded so no later agent has to re-derive them. In
every case `README.md` wins, per precedence.

| Point | `README.md` | Elsewhere in the bundle | Verdict |
| --- | --- | --- | --- |
| Dark `--heatmap-empty` | `#262230` | `#2a2a2a` in `components/heatmap/HeatmapFrame.prompt.md` | `#262230`. `tokens/heatmap.css` agrees with the README. |
| Results max width | 1180px | `--content-max: 1040px` in `tokens/spacing.css` | 1180px results, 1040px heatmap. The token is the heatmap value. |
| Form column cap | 380px | `--form-max: 460px` in `tokens/spacing.css` | 380px, per the index screen spec. |
| Figures | Gotham; "the serif gets the words, Gotham gets the numbers" | "serif number" in `StatBlock.prompt.md` and `.d.ts` | Figure face, not serif. Under the self-hosted mapping that is JetBrains Mono. |
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
