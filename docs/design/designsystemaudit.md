# Audit: Claude Design project `7d95e96a` against the shipped design system

Audit only. No code was changed. Nothing was pushed to the design project.
Derived from the stylesheets on branch `test` at `3f59380`, 2026-09-11.

---

## 0. What was readable, and what was not

`DesignSync` refused: the session has no design-system authorization and
`/design-login` cannot run non-interactively. The remote project was therefore
audited through the **verbatim local snapshot** at `docs/design/`, imported
2026-08-21 — 61 of the project's 207 files, including every file that carries a
value: `README.md` (the project's `readme.md`), `styles.css`, all ten
`tokens/*.css`, all 24 component `.prompt.md` + `.d.ts` pairs, and
`reference/audit-review.md` (the project's `ScrobbleScope UI Audit Review.html`).

**Seven of the named focus files could not be read at all**, because the import
deliberately excluded root tooling: `_ds_bundle.js`, `_ds_manifest.json`,
`_adherence.oxlintrc.json`, `SKILL.md`, `github.md`, `support.js`,
`thumbnail.html`. Anything those files assert is outside this audit. If
`_adherence.oxlintrc.json` lints against the token names in section 2, it is
lint-checking names that do not exist in this repository — see D-1.

To close that gap: run `/design-login` once in an interactive terminal, then
re-run this audit with `DesignSync list_files` + `get_file`.

---

## 1. Verdict

The project is **not merely out of date — its token layer never shipped in any
form.** Every one of the semantic custom-property families the project tells an
implementer to "port into the Tailwind config" appears **zero times** in the
nine live page stylesheets:

```
--surface-page  --surface-card  --surface-sunken  --text-strong  --text-body
--text-muted  --accent  --accent-soft  --accent-contrast  --border-default
--border-strong  --focus-ring  --space-1..12  --card-padding  --page-gutter
--content-max  --form-max  --radius-pill  --leading-*  --tracking-*
--text-data-*  --weight-*  --shadow-modal  --overlay-scrim  --blur-sticky
--logo-bar  --button-solid-*  --rocket-0..6  --rocket-ramp
--heatmap-cell-radius  --heatmap-cell-gap  --duration-*  --ease-*
--pinwheel-cycle  --ss-warn
```

The repository did not transcribe the design system; it **re-derived** it into a
different architecture (daisyUI theme slots plus an `--ss-*` set) and then moved
on. The design project has no record of that architecture, so it cannot be used
as a reference by anyone — agent or human — without producing code that silently
fails to resolve.

Severity summary:

| | Count |
| --- | --- |
| Token name families that are fiction in this codebase | 28 |
| Values that are stated and **wrong** (not just renamed) | 14 |
| Whole subsystems the project does not know exist | 4 |
| Incidental code defects surfaced while auditing | 4 |

The project is also **not the only stale document**. `docs/design/RECONCILIATION.md`,
the repo's own override list, is itself wrong in two places (D-15, D-16).

---

## 2. The actual design system

This is what to tell Claude Design. Source of truth, in precedence order:

1. `static/css/tailwind.src.css` — the `@theme static` block and the two
   `daisyui-theme.mjs` plugin blocks. **Every colour, type size, space step and
   radius in the migrated app is written here and nowhere else.**
2. `static/js/heatmap.js` — `ROCKET_STOPS` and the grid geometry constants.
3. `static/css/shell.css` — the header's own `--shell-*` palette (a second,
   independent copy; see section 4).
4. `static/css/global.css` — the Bootstrap-era `:root` / `.dark-mode` shim for
   the two unmigrated pages. Scheduled for deletion at WP-8.
5. `DESIGN.md` at the repo root — already a correct code-derived summary. It is
   the closest thing to a replacement for the project's `readme.md` and should
   seed the rewrite.

### 2.1 Token architecture — three layers, not one

The project describes a single flat layer of semantic aliases. Reality:

- **daisyUI slots** — `--color-base-100/200/300`, `--color-base-content`,
  `--color-primary`, `--color-primary-content`, plus `--radius-field/box/selector`.
  These carry the surfaces and the accent.
- **`--ss-*` extension set** — for the four roles daisyUI has no slot for, plus
  surfaces and status. The `ss-` prefix is **load-bearing, not cosmetic**:
  `--text-body` is already Tailwind v4's font-size namespace and
  `--text-body: 1rem` exists in `@theme`. A colour emitted under `[data-theme]`
  at the same name wins on specificity and silently breaks `.text-body`. This is
  the single most important fact the design project is missing, because its
  spec instructs exactly that collision.
- **Tailwind `@theme static`** — `--font-*`, `--font-weight-*`, `--text-*`,
  `--spacing-*`, `--radius-*`. `static` (not plain `@theme`) because handwritten
  CSS reads these directly; a plain `@theme` prunes unused tokens and an
  undefined `var()` with no fallback voids the whole declaration.

`--spacing` and `--spacing-*` are explicitly reset to `initial`, so Tailwind's
**dynamic spacing is off**: undeclared utilities like `w-10` emit no rule at all.
Any spec written as arbitrary Tailwind utilities will partly no-op.

### 2.2 Colour — shipped values

| Role | Live token | Light | Dark |
| --- | --- | --- | --- |
| Page | `--color-base-100` | `#faf7f0` | `#0e0c12` |
| Sunken | `--ss-surface-sunken` / `--color-base-200` | `#f0ebe0` | `#1a1622` |
| Card (general) | `--ss-surface-card` | `#f9f7f1` | `#181520` |
| Card (index standout) | `--ss-surface-card-standout` | `#ffffff` | `#181520` |
| Results / Unmatched panel | `--results-surface`, `--unmatched-surface` | `color-mix(base-100 50%, sunken)` | same formula |
| Strong text | `--color-base-content` | `#1a1820` | `#f1ede4` |
| Body text | `--ss-text-body` | `#4a4456` | `#c5bfb1` |
| Muted text | `--ss-text-muted` | `#6c6676` | `#908a9a` |
| Hairline | `--ss-border-default` | `#e5dfd1` | `#2a2434` |
| Index well divider | `--ss-border-divider` | `#8a867e` | `#68646f` |
| Accent | `--color-primary` | `#6a4baf` | `#b39dde` |
| On accent | `--color-primary-content` | `#faf8f3` | `#0e0c12` |
| Accent tint | `--ss-accent-soft` | `#efe9fa` | `#2a1f44` |
| Good | `--ss-good` | `#2f7a4a` | `#6fcf97` |
| Bad | `--ss-bad` | `#b03434` | `#e07070` |

Five surfaces ship, not three. There is no warn colour. daisyUI's generic
`--color-success / --color-warning / --color-error` still carry Bootstrap's
`#198754 / #ffc107 / #dc3545` — the design project must state that page
components use the `--ss-*` tokens and never the generic slots.

### 2.3 Type

Families and the 300/400/700 rule are **correct in the project and correct in
code** — the one part of the spec that survived intact, including the
`akzidenz-grotesk-next-pro` (not plain `-next`) requirement and the deletion of
`--font-weight-medium` / `-semibold`.

The **size ladder is entirely different.** Shipped, in rem, with paired
line-heights:

```
--text-label-sm  0.75rem / 1rem        --text-display     1.5rem / 1.75rem
--text-label     0.8125rem / 1rem      --text-display-lg  2rem / 2.25rem
--text-body-sm   0.875rem / 1.25rem    --text-display-xl  3rem / 1
--text-body      1rem / 1.5rem
```

Seven steps, not the project's thirteen across three ladders. There are no
`--text-data-*`, `--leading-*` or `--tracking-*` tokens. Letterspacing is
written inline and is **ungoverned**: 14 distinct values ship (0.12em, 0.08em
and 0.06em each five times, down to one-offs at 0.16em, 0.15em, 0.13em, 0.01em).

`static/css/results.css` defines a **second, parallel type scale** —
`--text-xs` through `--text-5xl`, each multiplied by `--results-scale`. The
design project has no concept of this.

Units are **rem for type and space, px for thin details**, by owner ruling
2026-08-24, overriding the project's px figures. Read the project's px as sizes
at a 16px root, never as units.

### 2.4 Space and radius

Space ships as `--spacing-1/2/3/4/6/8/12` = `0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 /
3 rem`. Same seven steps as the project, different names, rem not px.

Radius ships all five: `--radius-xs 4px`, `-sm 8px`, `-md 10px`, `-lg 14px`,
`-full 999px`. The project's `radius.css` header says "four values. Anything
else is a mistake" and then lists five — and names the pill `--radius-pill`,
which does not exist. daisyUI also carries its own `--radius-field 8px` /
`--radius-box 14px` / `--radius-selector 999px`, and `--radius-box` is consumed
directly by `unmatched.css`.

### 2.5 Elevation

Two shadows ship, both as theme tokens because dark raises the alpha:
`--ss-shadow-chip` `0 1px 3px rgb(0 0 0 / 0.06)` → `/ 0.4`, and
`--ss-shadow-float` `0 2px 8px rgb(0 0 0 / 0.15)` → `/ 0.4`. Both values match
the project exactly.

`--shadow-modal`, `--overlay-scrim` and `--blur-sticky` **do not exist**. The
"borders do the work" principle holds in code and should be kept.

### 2.6 Motion — the project's motion spec is fiction

No `--duration-*`, `--ease-*` or `--pinwheel-cycle` token exists. Motion is
written inline and is the least governed part of the system: **26 distinct
durations and 8 distinct easings** across the live sheets.

- Dominant real values: `0.2s` (16 uses), `160ms` (15), `0.3s` (7), `150ms` (5).
- Dominant easing: bare `ease` (49 uses), then `linear` (10),
  `cubic-bezier(0.42, 0, 0.58, 1)` (8), `ease-out` (7).
- The project's `--ease-out` `cubic-bezier(.22,.61,.36,1)` appears **nowhere**.
- The project's "content enter 500ms with a 20px rise" is wrong: the enforced
  value is the `ss-page-enter` keyframe at **0.22s**, pinned by
  `scripts/dev/frontend_gate.py`. The index fade is `--index-fade-duration: 180ms`.
- `2.5s` (pinwheel) and the five wordmark bar durations (1.6 / 1.7 / 1.9 / 2.1 /
  2.3s) **do** match the project.

`prefers-reduced-motion` is honoured in all nine page sheets.

### 2.7 Layout, measure, and the scaling system — absent from the project

Every measure in the project's screen specs is wrong, and the mechanism that
replaced them is undocumented there.

| Screen | Project says | Ships |
| --- | --- | --- |
| Index grid | `1.1fr 1fr`, uncapped | `1.1fr 1fr` at 860–1199px, **`3fr 4fr` at ≥1200px** |
| Index form cap | 380px | `calc(27.5rem * var(--index-scale))` |
| Index hero padding | 56px | `3.5rem` (= 56px; correct) |
| Results measure | 1180px | **`90rem`** (1440px) |
| Heatmap measure | 1100px | **`73rem` base, `min(84vw, 120rem)` from 860px** |
| Unmatched measure | 1180px | `73.75rem` (= 1180px; correct) |
| Heatmap inner text | — | `54rem` |

**The scaling system is the single largest omission.** Two pages scale their
whole composition from a numeric custom property:

- **Index** — `--index-scale`, pure CSS:
  `clamp(--index-scale-min 0.70, min(base 1.075 × tan(atan2(100vw, 1920px)),
  tan(atan2(100vh − shell-height, natural-height + gutters))),
  --index-scale-cap 1.75)`, with a softened slope above 1920px
  (`0.35 + 0.65 × ratio`). `--index-natural-height: 42.0625rem`, measured, not
  chosen. Consumed **102 times**; roughly every dimension on the page is
  `calc(<rem> * var(--index-scale, 1))`, with readability floors written as
  `max(0.75rem, …)`.
- **Results** — `--results-scale`, set by `static/js/results.js` as
  `max(1, pageWidth / (rootSize × --results-base-rem 75))`, updated on a
  `ResizeObserver`. Consumed **58 times** in CSS plus arbitrary Tailwind values
  in `results.html`. Small screens and no-JS stay at 1.

Breakpoints actually in use: **860px** (the one real layout break, written as
`859.98px` for max-width), 768px, 1200px, 1920px. The project names only 860px.

`html { scrollbar-gutter: stable; }` is load-bearing — without it Firefox shifts
the fixed-window composition when the form grows.

### 2.8 Theme mechanism

The project says `.dark` on `<html>`. Reality is a **dual write**, in
`static/js/theme.js`:

- `data-theme="light" | "dark"` on `<html>` — daisyUI and `shell.css` key on it
- `.dark-mode` on `<body>` — the Bootstrap-era page sheets key on it

`@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *))`
redefines Tailwind's `dark:` variant against the attribute. An inline script in
`base.html` sets the attribute before first paint, and `theme.js` reads the
decision back rather than recomputing it. The second write retires at WP-8.

Any `.dark { … }` selector in the project's token files is dead code here.

### 2.9 Heatmap

`ROCKET_STOPS` in `static/js/heatmap.js` is the only definition of the ramp, as
RGB triples, not CSS custom properties. The seven hex values match the project
exactly. Only one stop is mirrored into CSS, deliberately: `--rocket-5 #f0903a`,
for the Heatmap mode tab's mark. `--rocket-ramp` does not exist.

Geometry ships as JS constants, and **the project is wrong on two of three**:

| | Project | Ships (`heatmap.js`) |
| --- | --- | --- |
| Cell size | 11px (`HeatmapFrame.d.ts`) | `CELL_SIZE 14` |
| Cell radius | 2px | `CORNER_R 2` — correct |
| Desktop gap | 2px | `CELL_GAP 2` — correct |
| Mobile | "1px gap" | `MOBILE_GAP 1` plus a responsive cell sizer: target 22, min 18, max 28, columns 10–28 |

Surfaces diverge: `--heatmap-surface` is `var(--ss-surface-sunken)` `#f0ebe0` in
light (the project says `#faf8f3`) and `#181520` in dark (correct).
`--heatmap-empty` is **`#c8bfad`** in light — the project says `#e8e2d6`, which
the owner rejected on 2026-09-10 as insufficiently distinct on the sunken frame.
Dark `#262230` is correct.

---

## 3. Defect register

Each row is a place the design project must change. Nothing here was edited.

| ID | Area | Project asserts | Code is | Action |
| --- | --- | --- | --- | --- |
| D-1 | Token layer | 28 semantic token families to "port into the Tailwind config" | None exist; architecture is daisyUI slots + `--ss-*` + `@theme` | **Rewrite `tokens/*.css` wholesale** to the three-layer architecture in 2.1. Highest priority: anything generated from the old names cannot resolve. |
| D-2 | Token naming | `--text-body`, `--text-muted` as colours | Collides with Tailwind v4's font-size namespace; must be `--ss-text-body` etc. | Add the collision rule as a hard constraint |
| D-3 | Light page | `--surface-page #faf8f3` | `#faf7f0` (owner warmed it 2026-09-09) | Correct the value |
| D-4 | Light muted | `--text-muted #6f6a7a` | `#6c6676` (owner readability floor) | Correct the value |
| D-5 | Card surface | `#ffffff`, one card colour | Split: `#f9f7f1` general, `#ffffff` index standout only, plus a `color-mix` midpoint on Results/Unmatched | Replace with the five-surface model |
| D-6 | Status | `--ss-warn #b35a1f` / `#e0a458` | No warn colour ships; no consumer | Drop it, or mark it unshipped |
| D-7 | Label size | `--text-label 11.5px` | `0.8125rem` (13px); small-label floor is 12px | Correct, and state the 12px floor |
| D-8 | Type ladder | 13 sizes across 3 ladders, px | 7 steps with paired line-heights, rem | Replace the ladder |
| D-9 | Units | px throughout | rem for type and space, px for thin details (owner ruling 2026-08-24) | Restate; WCAG 1.4.4 / technique C14 is the reason for the type half |
| D-10 | Motion | 5 duration tokens, 2 easings, "enter 500ms + 20px rise" | No tokens; 26 durations, 8 easings; enter is 0.22s | Rewrite as observed values, and flag motion as the system's weakest area |
| D-11 | Theme marker | `.dark` on `<html>` | `data-theme` on `<html>` **and** `.dark-mode` on `<body>` | Correct; note the second write dies at WP-8 |
| D-12 | Measures | Results 1180 / Heatmap 1100 / form 380 | 90rem / 73rem→min(84vw,120rem) / 27.5rem × scale | Correct all three |
| D-13 | Scaling | Not mentioned | `--index-scale` (102 uses, pure CSS) and `--results-scale` (58 uses, JS) | **Add as a new first-class section.** Largest omission. |
| D-14 | Heatmap | cell 11px, surface `#faf8f3`, empty `#e8e2d6` | cell 14px, surface `#f0ebe0`, empty `#c8bfad` | Correct; keep radius 2 and gap 2, which are right |
| D-15 | Heatmap gap (repo doc) | `RECONCILIATION.md` §7 says shipped is "14px cell, **3px gap**" | `CELL_GAP = 2` | `RECONCILIATION.md` is stale — the gap now agrees with the design project |
| D-16 | Index grid (repo doc) | `RECONCILIATION.md` says "current source declares `3fr 4fr`" | Both: `1.1fr 1fr` at 860–1199px, `3fr 4fr` at ≥1200px | `RECONCILIATION.md` is stale — the project's `1.1fr 1fr` is right for one band |
| D-17 | Figure face | "Gotham gets the numbers, the serif gets the words. They never compete." | Heatmap, Loading, Unmatched and Error use `--font-figure`; **Results uses `font-serif` for all four stat figures** | One of the two must give — narrow the rule, or treat Results as a defect. Owner ruling needed |
| D-18 | Bundle self-contradiction | `Button.prompt.md`, `Button.d.ts`, `Input.d.ts` say "JetBrains Mono" | Input Mono, per the Adobe kit | Fix those three files; everything else they specify stands |
| D-19 | `radius.css` header | "four values. Anything else is a mistake", then lists five | Five ship | Fix the count; name the pill `--radius-full`, not `--radius-pill` |
| D-20 | Dynamic spacing | Spec written as Tailwind utilities | `--spacing-*: initial` disables dynamic spacing; `w-10` emits nothing | State it — specs using arbitrary utilities will partly no-op |
| D-21 | Header pills | "prototype scaffolding — do not build them" | Production navigation: Home, Heatmap, Results, Unmatched | Correct; the header is in document flow, not fixed |
| D-22 | Copy | Heatmap H1 "A year of listening, *one grid.*"; mode card "always covers… No other settings."; "Album release filter" | "Your last 365 days, *one grid.*"; "Your listening heatmap covers the last 365 days."; "Release filter" | Correct all three |
| D-23 | Loading | "a progress bar" | One slim determinate hairline; the pinwheel is status motion only | Correct; the "exactly one progress signal" rule survives |
| D-24 | Lockup | viewBox `0 0 453 69` | `0 0 453 74` — 69 clips the `p` descender in "Scope" | Correct the canonical asset; three tests in `tests/test_template_shell.py` pin it |
| D-25 | Breakpoints | 860px only | 768, 860, 1200, 1920 | Add the other three |
| D-26 | Components | 24 specified, incl. Tooltip and SegmentedControl | daisyUI include list is `button, card, modal, toggle, input, select, tab, toast, alert`; no tooltip or segmented-control markup in templates | Mark the unbuilt components as unbuilt rather than as spec |

### Correct, and worth keeping verbatim

Type families and the no-500 / no-600 rule · `akzidenz-grotesk-next-pro` over
the plain family · Input Mono Narrow for 9–11px letterspaced caps · the seven
`rocket_r` hexes · dark surfaces `#0e0c12` / `#1a1622` / `#181520` · dark text
`#f1ede4` / `#c5bfb1` / `#908a9a` · the accent pair `#6a4baf` / `#b39dde` ·
accent tint `#efe9fa` / `#2a1f44` · hairline `#e5dfd1` / `#2a2434` · body text
`#4a4456` / `#c5bfb1` · the good / bad pairs · both shadow values · the seven
spacing steps as sizes · the five radii as sizes · "borders do the work, not
shadows" · hero padding 56px · Unmatched 1180px · heatmap cell radius 2px and
desktop gap 2px · pinwheel 2.5s and the five bar durations · no zebra striping ·
the accent is only ever the user's own data, never the year.

---

## 4. Incidental code defects found while auditing

Not the design project's problem. Reported, not fixed.

1. **`--ss-shadow-card` is never defined.** `static/css/heatmap.css` reads
   `box-shadow: var(--ss-shadow-card, none)` and no theme block declares the
   token, so the fallback always wins and the declaration is dead. Either define
   it or delete the rule.
2. **`--bars-color` diverges in dark on the legacy pages.** `global.css`
   `.dark-mode` sets `#9370db`; the theme's dark primary is `#b39dde`. The
   comment directly above it says "Keep the two equal — Batch 21's acceptance
   gate compares `--bars-color` with the theme primary." Light agrees at
   `#6a4baf`; dark does not. Worth confirming whether the gate checks both
   themes.
3. **`--shell-accent-ink: #ffffff` vs `--color-primary-content: #faf8f3`.**
   `shell.css` carries a parallel hard-coded palette; this one value does not
   match its theme counterpart.
4. **`--ss-shadow-chip` has no consumer** in any page stylesheet, though the
   frontend gate asserts its value in both themes.

---

## 5. Remediation plan for the design project

No writes were made. Recommended order, smallest blast radius first:

1. **Land the pure value edits** — D-3, D-4, D-7, D-14, D-19, D-22, D-24. Low
   risk, and it immediately stops an agent shipping a rejected colour.
2. **Fix the three files that say JetBrains Mono** (D-18) and mark the unbuilt
   components (D-26). Self-contradiction inside the bundle is worse than
   staleness, because precedence cannot resolve it.
3. **Replace `tokens/` wholesale** (D-1, D-2, D-5, D-6, D-8, D-9, D-10) against
   `static/css/tailwind.src.css`. This is the bulk of the work and the only item
   that makes the project safe to reference. `DESIGN.md` at the repo root is
   already a correct code-derived summary and should seed it.
4. **Add the two sections the project has no concept of** — the scaling system
   (D-13) and the real breakpoint set (D-25) — and correct every measure (D-12).
5. **Get an owner ruling on D-17** (serif vs Gotham for the Results figures)
   before writing either rule down, since the code is currently inconsistent
   with itself across pages.
6. **Re-run this audit through `DesignSync`** once `/design-login` has run, to
   cover the seven root tooling files and the 146 unimported files — in
   particular whether `_adherence.oxlintrc.json` lints against the dead token
   names.
7. Correct `docs/design/RECONCILIATION.md` §7 and its override table (D-15,
   D-16) in the same pass, so the repo's own override list stops disagreeing
   with the code it overrides.

---

# Revision, same day: after a full read of DESIGN.md, docs/design/README.md, global.css, shell.css and results.css

The first pass read those five files partially and by grep. Reading them end
to end changed six findings and added eight. Everything in sections 1–5 above
still stands except where contradicted here.

## Corrections to the register

- **D-17 was mischaracterised.** The serif figures on Results are
  **deliberate**, not an oversight. `results.css` says "Match the deployed
  stat roles: mono labels, sans captions, serif values" — a considered
  restoration of the shipped look. The metric column also splits by *kind*:
  `.metric-val-plays` is serif, `.metric-val-playtime` is mono-narrow.
  `--font-figure` is unused on Results entirely. The owner ruling is still
  needed, but the question is "does the Role Segregation Rule narrow?", not
  "is Results broken?".
- **D-25 understated the count.** Not four breakpoints — **eight**:
  767.98, 768, 859.98, 860, 1024, 1200, 1920, and 60.3125rem (965px). The
  handoff's "Single breakpoint at 860px" is wrong by seven.
- **D-14 extends to `--rocket-5`'s role.** Both the handoff *and* DESIGN.md
  say it is "used exclusively for the Heatmap mode indicator mark". It has
  four consumers across three pages: the index mode-tab mark, an
  `empty.css` gradient stop, and `.album-link` / `.rank-link` hover on
  Results — the latter with a hardcoded `rgba(240,144,58,…)` glow and tint
  that must track the token by hand.
- **D-10 was too harsh in one place.** Three of the old motion values
  described something real, even though the tokens were fictional: the theme
  swap genuinely is 300ms (7 uses), the pinwheel genuinely is 2.5s, and the
  legacy `#logo-wrapper svg` fade genuinely is 2s — the old
  `--duration-logo: 2000ms`. Only "enter 500ms with a 20px rise" was
  invented: the real entrance is `ss-page-enter` at **220ms ease-out,
  opacity only, no rise**, with `ss-page-exit` at 140ms ease-in.
- **D-26 was wrong about the tooltip.** A tooltip does ship —
  `.album-link-tooltip` in `results.css`, position: fixed, z-index 1040,
  120ms opacity+visibility. It is hand-built, not a daisyUI component, which
  is why the include-list grep missed it.
- **D-5 needs one addition.** `--results-surface` and `--unmatched-surface`
  are the same `color-mix` formula declared twice in two files rather than
  one shared token.

## New defects

| ID | Area | Finding |
| --- | --- | --- |
| D-27 | Header geometry | The handoff says the header is "68px desktop / 60px mobile — **fixed**, so the wordmark sits at the same vertical position on every screen". All three facts are wrong: `--shell-height` is `clamp(4.25rem, 2.96875vw, 4.75rem)` (68→76px), mobile is **4.25rem (68px, not 60)**, and the header is `position: relative` in document flow and scrolls away. The wordmark does *not* hold one position across screens. |
| D-28 | Brand marks | **The design system has no record of the single most failure-prone rule in the shipped CSS.** The SVG asset pins `stroke: #6a4baf` in its own `<style>` and its letterforms carry no fill rule, so every wrapper must be named in an explicit recolour rule. Miss one and you get fixed-purple bars and user-agent black text — which is exactly what shipped on the index hero: black letterforms on the `#0e0c12` dark page, unreadable (F-B21-21). `check_mark_follows_theme` in the frontend gate exists solely to catch this. |
| D-29 | Lockup sizing | The header lockup is `height: clamp(1.75rem, 3.9vw, 2.5rem)`, flat 2.5rem from 965px. Not cosmetic: between 860 and ~965px the bar cannot fit a 245px lockup + a 489px nav at its floor + a 159px toggle, so content overflowed for that entire 105px band. Absent from the handoff. |
| D-30 | Gate-pinned values | Several header dimensions cannot be changed freely — the nav link's `5.75rem` min-width floor (at 1920px the 4.53vw term is only 87px, so the ruled 92px comes from the floor; lowering it measured 88.4px at 1080p and fails `_header_geometry_failures`) and the toggle's `0.2rem` padding + 1px border, the 8.4px of chrome the toggle-height curve adds. The design system records none of them, so a plausible-looking edit fails CI. |
| D-31 | Elevation inventory | Four untokenised shadows ship beyond the two tokens: the theme toggle's **inset** `0 1px 2px` (0.04 light / 0.2 dark), the active choice's `0 1px 3px` (0.12 / 0.35), `.rank-link`'s `text-shadow: 0 0 8px rgba(240,144,58,0.45)`, and the spotlight scrim gradients in `rgba(14,12,18,…)`. The active-choice pair is the selected-segment case `--ss-shadow-chip` was drawn for, at a different alpha. |
| D-32 | Components | **Artist Spotlight is an entire component the design system does not contain** — `.spotlight-card-bleed`, `-content`, `-scrim-top`, `-scrim-bottom`, `-no-image`, plus back-compat aliases. 24 components are specified; this is a 25th, shipped. |
| D-33 | Focus | One real exception to "2px offset, non-negotiable": `.metric-toggle-btn:focus-visible` uses `outline-offset: 1px`. |
| D-34 | Selection + scrollbars | `::selection` diverges by page family — `--ss-accent-soft` on migrated pages, `--info-bg` (accent at 10% alpha) on the two Bootstrap ones, which also set `* { scrollbar-color: var(--border-color) transparent }`. Retires with `global.css` at WP-8. |

## DESIGN.md is not fully accurate either

It is the best source in the repo and should still seed the rewrite, but
four claims do not hold:

1. **Modal Shadow** (`0 24px 60px -24px rgb(20 18 30 / 0.4)`) is listed in
   the Shadow Vocabulary. No such shadow exists in any stylesheet.
2. **The Border-Over-Shadow Rule** cites `1px solid var(--border-default)` —
   a token that does not exist. It is `--ss-border-default`.
3. **"Desktop Index Stage: `3fr 4fr`"** omits that 860–1199px is
   `1.1fr 1fr`. Two grids ship, not one.
4. **`--rocket-5` "used exclusively for the Heatmap mode indicator mark"** —
   see the correction above.

## New incidental code defect, and it breaks a named rule

5. **Two `font-weight: 500` declarations ship**, both in `shell.css` — the
   theme toggle's active pill in light mode (`.site-header__theme-choice--light`)
   and in dark mode. The Adobe kit serves **300/400/700 only**, so both
   render a browser-synthesized fake weight. This violates The No-Medium
   Rule, which DESIGN.md states as a named rule and `tailwind.src.css`
   enforces structurally by deleting `--font-weight-medium` and
   `-semibold` from the theme. Every other weight in the nine page
   stylesheets is 400 or a token — these are the only two. The active pill
   already carries a border, a background and a shadow, so the fake weight
   is doing no work the other three cues aren't.

This brings the incidental code-defect count to five: the undefined
`--ss-shadow-card`, the dark `--bars-color` divergence (now measurable —
`global.css` `.dark-mode` uses `#9370db` and the marks on loading/results/
unmatched render at `#f8f9fa`/`#9370db` against the migrated
`#f1ede4`/`#b39dde`), the `--shell-accent-ink` mismatch, the unconsumed
`--ss-shadow-chip`, and these two `font-weight: 500`s.

---

# Cross-verification against templates, JS and git history

The first two passes read CSS. This pass read `base.html`, `index.html` and
`_loading.html` in full, `page_motion.js` and `unmatched.js` in full, the
validation half of `index.js`, the component class inventory across all 13
templates, and `git blame` + commit messages on the contested lines. It
answers the question CSS alone could not: **was this intentional, and how was
it written down?**

The answer splits three ways, and section B is the one that changes the
remediation plan.

## A. Deliberate, recorded in code — the design system is simply stale

Not drift. Each carries an in-code rationale, and in every case the design
system should be corrected to match the code.

| Divergence | Design system says | Code does, and says why |
| --- | --- | --- |
| Hero capability marks | "three mono capability marks each prefixed with a purple arrow" | `§ 01 / § 02 / § 03` section marks. A section sign, not an arrow — it reads as a legal/archival mark, which is DESIGN.md's "field notebook / monograph" north star expressed as a glyph. Wholly intentional. |
| Album-mode lede | "Rank a single year, a whole decade, or your entire history…" | Rewritten. Commit `14215d65` states the purpose: "Album mode lede rewritten to remove jargon ('specialized data visualization', 'Enrich your scrobbles with Spotify metadata', 'isolate custom release eras') in favour of a plain workflow description." |
| Username validation | "green check when >2 chars" | The check ships (`\2713` via `:has()` in `--ss-good`) but fires **on blur after a `/validate_user` round-trip**. The green state means "Last.fm confirms this account exists", not "long enough" — a materially stronger signal, with a generation counter so a stale response cannot overwrite a newer username's verdict, and a 5xx treated as "the service failing, not a verdict". |
| Year validation | implied the same treatment | `index.js` line 36, verbatim: "Year inline warning (no green/checkmark — only shows on error)". Positive confirmation was deliberately withheld where there is nothing to confirm. |
| Filter tags on Results | "four outline tags echoing the active filters" | `.results-filter-bar`, commented "Micro-data filter bar: tucked left, text in mono-narrow, **no bold, no pills**". Tag-as-pill was considered and rejected. |
| Album rows | "`AlbumRow`: rank, 38–44px cover at 4px radius… rows separated by 1px dividers" | A `<table class="results-table">` with `table-layout: fixed` and four columns, because the wrapper's `overflow-x-auto` gave phones a sideways scrollbar with content hidden off-screen and no affordance (owner ruling 2026-09-09, "no horizontal scroll at any width"). Covers are **4rem / 4.5rem at `--radius-sm` (8px)**, not 38–44px at 4px. |
| Loading progress | README: "a progress bar" | The bar is `role="progressbar"` with full `aria-value*` and **stays `.hidden` until polling returns a real determinate value**; the phase line is a separate `role="status" aria-live="polite"`. This implements `ProgressBar.d.ts`'s own "Only show it when the value is real; otherwise show the pinwheel alone" — so the code follows the **audit-review** position over the README's. Part of F-B21-4 is already settled in code. |
| Help affordance | "`?` in a circle for tooltips" | No `?` control anywhere. The idiom is `.field__label-row` (label + hint), a `.field__help` paragraph, and `<small>` under threshold labels. Errors are `.field__error` with `role="alert"`, created in JS; the Bootstrap classes it used to carry "left the page with Bootstrap". |

## B. The design system won — one recorded case

Worth knowing because it runs the other way, and an indiscriminate "code wins"
rewrite would destroy it. From `index.html`:

> `limit_results` is a visible field above, not a row inside here.
> `BATCH21_DEFINITION.md` decision 3 relocated it into this disclosure; the
> owner ruled on 2026-08-24 that **the design's placement wins**, because how
> many albums you list is not part of what counts as listened and the label
> would then describe two of the three things it holds.

So precedence is not "code over design" as a rule. It is "whoever was ruled on
last" — and those rulings live in code comments, not in any index. Any rewrite
of the design project has to read the comments, not just the declarations.

## C. Never built, or silently dropped

| Item | Status |
| --- | --- |
| `Modal` | **Not built.** No modal markup in any of the 13 templates. daisyUI's `modal` sits in the include list unused, and `global.css` still styles a Bootstrap modal nothing renders. So the `Modal` spec, `--shadow-modal` and `--overlay-scrim` all describe an unbuilt component — which is why D-31's scrim gradients are the nearest thing that ships. |
| Eyebrow placement | The spec orders it wordmark → eyebrow → h1. The DOM is h1 → `<p class="eyebrow">` → lede, consistently in both modes. **The one divergence in this pass with no evidence of intent on either side.** |

**Retracted: the decade-pill disabled state.** I claimed it was never
implemented. It is — see the correction below. The error was grepping
`disabled` in `index.html` and stopping there; the state is applied
dynamically from `index.js`, which I had only read the validation half of.

## Retractions to D-26

My component grep was keyword-based and wrong twice over. Verified by class
inventory, **21 of the 24 specified components are built** — the spec is far
better implemented than I reported.

- **`SegmentedControl` IS built** — `.seg` / `.seg__radio` / `.seg__option`,
  radio+label pairs. I had grepped for the word "segmented".
- **`Tooltip` IS built** — `.album-link-tooltip`.
- Also built and initially missed: `Field`, `Stepper` (`.stepper__btn` with
  `−`/`+` glyphs and aria-labels), `PillGroup` (`.decade-pills`), `Disclosure`
  (native `<details>`, plus a `.th-reset` the spec never mentions), `Alert`
  (`.index-alert role="alert"`), `Toast` (daisyUI `toast toast-end
  toast-bottom`, JS-populated), `Pinwheel`, `Wordmark`, and `ModeTabs`
  (`role="tablist"` with real `<button>`s — a deliberate a11y fix closing
  F-B18-12 and the `span[role=button]` item in F-B21-5).
- Genuinely not built: **`Modal`**. Partly: `SectionHeading` (three per-page
  headline classes plus `.eyebrow`, no single component), `AlbumRow` (became a
  table), `Tag` (became plain text).
- Shipped but absent from the spec: **Artist Spotlight**, an unmatched
  **expander** (`.unmatched-expander-btn`, "Show all N albums" / "Show fewer",
  `aria-expanded` toggled), and **artist-portrait hydration** via
  `/api/artist_spotlight` with an `IntersectionObserver` at `rootMargin: 100px`
  that replaces an initials fallback only after the image loads. The
  `UnmatchedGroup` spec has none of this.

## The two `font-weight: 500`s — intent checked, and it makes them worse

`git blame` puts both at `14215d65`, 2026-09-06, and the same commit sets
`font-weight: 400` explicitly on the *inactive* choice. So the author was
deliberately using weight as the active/inactive contrast. This is a considered
choice, not a typo.

But that commit's message is *"style: clarify hero copy, fix heatmap eyebrow,
add page-load fade"* and never mentions the theme toggle. The restyle rode
along inside an unrelated commit with no recorded rationale, and the kit has no
500, so both render a synthesized fake. **A fix must preserve the
active/inactive distinction the commit was reaching for** — though the active
pill already carries a border, a background and a shadow, so dropping to 400
loses nothing the other three cues are not already saying.

That same commit also describes an arrival mechanism the code no longer uses
("body opacity:0 → body.is-ready opacity:1 … triggered from base.html on
DOMContentLoaded"). It was later reworked into the CSS-owned `body > main`
animation that now explicitly warns "Do not wait for DOMContentLoaded". Which
leaves two loose ends:

## New incidental code defects from this pass

6. **`is-ready` is dead.** `page_motion.js` adds
   `document.body.classList.add('is-ready')` on both `DOMContentLoaded` and
   `pageshow`, and **no stylesheet or test reads it** — a leftover from
   `14215d65`'s abandoned body-opacity approach. Only `is-leaving` is consumed.
   Harmless, but it reads as load-bearing.
7. **The 140ms exit duration is a coupled pair with no comment saying so.**
   `shell.css` animates `ss-page-exit` at 140ms; `page_motion.js` independently
   hardcodes `setTimeout(…, 140)` as its navigate fallback. Change one and
   navigation either jumps early or hangs past the fade. Neither side mentions
   the other.

## Architectural facts neither document records

Both belong in the design system, because an agent generating a page will
violate them:

- **Exactly one framework stylesheet per page.** `base.html`: "Bootstrap and
  daisyUI both claim `.btn`, `.card` and `.modal`, and Tailwind's preflight
  would reset a Bootstrap page." The `legacy_css` block **defaults to ON**, so
  an unmigrated page keeps its theme by doing nothing and a migrated page
  overrides it with an empty block — "that way forgetting is safe; the opposite
  default loses a page's theme silently and no test catches it."
- **Shared partials must be framework-neutral.** `_loading.html`: every class
  is first-party, no Bootstrap and no daisyUI class, because a shared partial
  cannot know which framework its host page carries. It also depends on two
  things the host must supply — styles for `.wait-panel` / `.ss-btn`, and a
  `.hidden` utility (Tailwind generates it; a Bootstrap host must define it or
  the error block shows from first paint) — and it parameterises its element
  ids because `heatmap.js` and `loading.js` read different ones.

## One behaviour that wants a ruling, not a correction

The pre-paint script in `base.html` reads
`saved === 'true' || (saved !== 'false' && prefers-color-scheme: dark)`. The
theme follows the system preference until the toggle is used **once**, after
which the stored `'false'` wins permanently. That is correct logic for "an
explicit choice beats a system hint", so F-B21-22 is really asking for a third
"System" state rather than reporting a broken selector. The logic is right; the
state machine has two states where it may want three.

---

# Correction: the decade pills are implemented, and the spec has the rule backwards

I reported the disabled state as never implemented. That was wrong, and the
method was the problem: I grepped `disabled` in `index.html`, found nothing,
and concluded nothing existed. The state is applied dynamically from
`index.js` — `updateDecadePills()` — which I had only read the validation half
of. A static-markup grep cannot see a dynamic state; that is the same class of
error as the `SegmentedControl` retraction.

## What actually ships

```js
// A decade is impossible if it starts AFTER the listening year
// e.g. listening in 2016, "2020s" starts at 2020 — impossible
const impossible = decadeStart > listeningYear;
radio.disabled = impossible;
decadeLabels[i].classList.toggle('decade-pill-disabled', impossible);
```

Bound to the listening-year field's `input` event, so the pill set re-evaluates
as the reader types. Four behaviours, none of them in the design system:

1. **The rule is forward-looking, and the spec's is backward.** The handoff says
   "2020s→1950s, **pre-1970s disabled**" — old decades unavailable, a fixed
   floor. The code disables decades that start *after* the listening year: a
   ceiling, recomputed per input. Listening in 2016 disables the 2020s; nothing
   disables the 1950s. So this is not a stale value, it is **the opposite
   direction**, and the shipped rule is the correct one — an album cannot be
   released after the year you listened in, whereas a 1950s album is perfectly
   possible at any listening year. Correct the spec, do not restore its floor.
2. **Reset when the year is unusable.** Fewer than 4 digits or no value re-enables
   every pill and hides the warning, rather than leaving a stale disabled set.
3. **Auto-recovery with an explanation.** If the *selected* decade becomes
   impossible, the first still-valid pill is checked and a warning appears:
   "Selected decade was adjusted — albums from that decade couldn't exist in
   your listening year." That is the Unmatched screen's tone benchmark applied
   to a form control — say what changed, and why — not a silent correction.
4. **A second, independent guard on the year field.** `registeredYear` from
   `/validate_user` sets `yearSelect.min`, rewrites the hint to `joined YYYY`,
   and on violation says "This user joined Last.fm in YYYY. Year must be YYYY
   or later." The two guards are complementary: the join year bounds the
   *listening year*, the listening year bounds the *decades*.

## The styling carries a rule worth promoting

`index.css` does not hide an impossible pill:

```css
/* Kept visible, not removed. A dimmed decade tells the reader the decade
   exists and holds nothing, which a missing pill does not. */
.decade-pill.decade-pill-disabled { opacity: 0.4; cursor: not-allowed; }
```

**Disabled is not hidden.** This is a genuine content/IA principle — the same
instinct as the Unmatched screen existing at all, and the same instinct behind
the year warning above — and the design system states it nowhere. It belongs
next to the existing named rules, because an agent generating a pill group will
otherwise filter the impossible options out of the list.

One caveat on the implementation, not the design: `updateDecadePills()` pairs
`decadePills[i]` with `decadeLabels[i]` by index across two separate
`querySelectorAll` calls. That holds only while the template keeps one
`.decade-radio` immediately before each `.decade-pill` in the same order — true
today, and silent if it ever stops being true.

## What this changes about the audit

Section C now has one confirmed entry, not two: `Modal` is unbuilt, and the
eyebrow placement remains the single divergence with no evidence of intent
either way. The decade pills move into section A — deliberate, recorded in
code, design system stale — and they are the strongest case in that section,
because the spec is not merely out of date but inverted.

It also lowers my confidence in any remaining "not built" claim that rests on
template markup alone. The three still standing — `Modal`, and the reshaped
`AlbumRow` and `Tag` — were each verified by class inventory across all 13
templates plus the page stylesheets rather than by a keyword grep, and `Modal`
additionally by the absence of any modal markup at all. But the JS I have still
not read (`loading.js`, `results-spotlight.js`, `loading-progress.js`, and
`heatmap.js` past line 40 — roughly 1,900 lines) can apply states and build
markup the templates never mention, exactly as `index.js` did here. Those four
files are the remaining gap, and the heatmap and loading sections of any rewrite
should not be treated as verified until they are read.

---

# Reframing: aesthetic divergence on migrated pages is intentional

Owner clarification, 2026-09-11. This is the frame the whole audit should be
read through, and it changes what counts as a finding.

**The design system is not the aesthetic authority for a migrated page.** Where
a migrated page looks different from the handoff, the page is right and the
document is behind. That is the migration working as intended, not drift to be
corrected in code.

So the audit's centre of gravity moves. It is not "14 values are wrong." It is
**"28 token-name families do not resolve, and four mechanisms are unrecorded."**
Those are mechanical failures — they break regardless of what the intended look
is — and they are the part worth spending effort on.

## Reclassified: not defects, just a stale record

Every one of these should still be **updated** so the document reflects current
aesthetics, but the direction is code → document, no ruling required, and none
of them is a problem in the code:

D-3 (light page `#faf7f0`) · D-4 (muted `#6c6676`) · D-5 (five surfaces) ·
D-6 (no warn colour) · D-7 (13px label, 12px floor) · D-8 (seven-step ladder) ·
D-12 (measures) · D-14 (heatmap surfaces and empty cell) · D-22 (copy) ·
D-23 (loading hairline) · D-27 (header height) · D-31 (shadow inventory) ·
and all eight rows of section A above.

**D-17 is withdrawn as a question.** I asked for an owner ruling on the serif
figures on Results. That ruling is already given by this clarification: Results
is migrated, its figure face is an intentional aesthetic choice, and
`results.css` records the reasoning ("Match the deployed stat roles"). The
Role Segregation Rule should be restated as applying to the handoff's own
aesthetic, not as a constraint migrated pages are violating. No ruling needed.

**D-33 (the 1px focus offset) drops to cosmetic.** Likewise the eyebrow
placement in section C — an aesthetic ordering choice on a migrated page needs
no rationale to be legitimate.

## Survives the reframing unchanged — these are mechanical

None of these is about how anything looks:

- **D-1 / D-2 — the token names.** An agent writing `var(--surface-page)`
  produces a declaration that resolves to nothing, and an undefined `var()` with
  no fallback voids the whole declaration. `--text-body` as a colour actively
  breaks the `.text-body` utility by specificity. This is the finding.
- **D-20 — dynamic spacing is off.** Already proven by consequence, not theory:
  `results.css` records that the WP-5 rebuild lost its stat-cell padding because
  `px-1.5 py-2.5` and `gap-1.5` compile to nothing. Aesthetic intent cannot
  rescue a rule that was never emitted.
- **D-13 — the scaling system.** `--index-scale` (102 consumers) and
  `--results-scale` (58, JS-driven). A generated page that ignores it is not
  differently styled, it is unscaled.
- **D-28 — the mark recolour.** Not an aesthetic preference: miss a wrapper and
  you ship black letterforms on a near-black page. It already happened.
- **D-30 — gate-pinned geometry.** A plausible edit fails CI.
- **D-18 — "JetBrains Mono" in three component files.** A wrong family name,
  not a different taste.
- **D-19 — `--radius-pill`** does not exist; it is `--radius-full`.
- **The decade-pill rule direction** — logic, not aesthetics. The spec's floor
  is inverted relative to the shipped ceiling.
- **The two `font-weight: 500`s.** The distinction between this and intentional
  divergence is the whole point: the kit ships no 500, so the declaration cannot
  be honoured at all. It is not an aesthetic the system should adopt; it is a
  synthesized fake.
- **The architectural facts** — one framework stylesheet per page,
  framework-neutral partials, the `.hidden` dependency, the 140ms coupling.

## New finding, and it is the largest of this pass: the migration is complete

All **eight** page templates override `legacy_css` with an empty block:

```
error.html  heatmap_empty.html  index.html  loading.html
results.html  results_empty.html  unmatched.html  unmatched_empty.html
```

`base.html` is the only file that references Bootstrap or `global.css`, and
every child suppresses it. **No page loads Bootstrap. No page loads
`global.css`.** There are zero unmigrated pages.

That retires a premise running through the repo's own comments. `shell.css`,
`global.css`, `theme.js` and `tailwind.src.css` all explain themselves in terms
of "the two remaining Bootstrap pages" or "an unmigrated page never loads the
compiled sheet." That condition no longer holds, so:

1. **`global.css` (486 lines) is dead code.** Nothing loads it.
2. **My incidental defect #2 was wrong about impact, and I should correct it
   plainly.** The `--bars-color: #9370db` divergence in `.dark-mode` is
   *unreachable* — it lives in a file no page loads. It is dead code, not a live
   colour bug. The same applies to the `::selection`/`scrollbar-color`
   divergence I logged as D-34: both sides of it cannot render, so D-34 is
   void.
3. **The `.dark-mode` write in `theme.js` is dead.** It toggles a class that no
   loaded stylesheet styles. The dual-write's stated purpose — "the seven legacy
   stylesheets still key on it" — has expired.
4. **The `--shell-*` duplication's rationale has expired**, but the tokens
   themselves are live, because the header renders on every page. So incidental
   defect #3 stands and is genuinely live: `--shell-accent-ink: #ffffff` against
   `--color-primary-content: #faf8f3`. With the "framework-neutral" reason gone,
   `shell.css` could read the theme directly.
5. **WP-8's precondition is already met.** The repo says WP-8 retires
   `global.css` "once no Bootstrap page is left." That is now, not later.

One thing I checked rather than assumed: the 18 `.btn` usages in migrated markup
are **fine**. daisyUI's `button` is in the `include` list and its `.btn` is
compiled into `tailwind.css` (36 rules), so those classes resolve to daisyUI,
not to an absent Bootstrap. Nothing is unstyled.

## Revised remediation order

The aesthetic reclassification makes this shorter and removes both blocking
questions.

1. **Rewrite `tokens/` against `tailwind.src.css`** — D-1, D-2, D-20. The only
   item that makes the project safe to reference at all. The eleven files staged
   in `scratchpad/ds-push/` do this.
2. **Add the unrecorded mechanisms** — the scaling system (D-13), the real
   breakpoint set (D-25), the mark-recolour requirement (D-28), the gate-pinned
   geometry (D-30), and the two architectural rules. These are what stop
   generated code from being broken rather than merely off-brand.
3. **Fix the names that are simply wrong** — D-18 (JetBrains Mono in three
   files), D-19 (`--radius-pill`), and the inverted decade rule.
4. **Refresh the aesthetic record from code** — the whole reclassified list
   above, plus DESIGN.md's four bad claims. Mechanical transcription, no
   judgement calls, and safe to do in bulk *except* for the one case in section
   B where the design system won the ruling: read the code comments, not just
   the declarations.
5. **Separately, in the repo:** the two `font-weight: 500`s, the dead
   `is-ready`, the undefined `--ss-shadow-card`, the 140ms coupling, and the now
   fully dead `global.css` plus the `.dark-mode` write. None of these is the
   design project's problem, and WP-8 can start today.

No blocking questions remain.

---

# The four unread JS files

`loading-progress.js`, `results-spotlight.js`, `loading.js` and `heatmap.js`
(all 1,446 lines), read 2026-09-11. They were the right gap to close: one
finding **corrects a claim I made two sections ago**, and the heatmap's mobile
rendering turns out to be a different chart type than either document describes.

## 1. Correction: the `.dark-mode` write is NOT dead

I said the dual-write in `theme.js` "toggles a class that no loaded stylesheet
styles" and called it dead. Wrong — it is load-bearing, just not through CSS.
`heatmap.js`:

```js
function initDarkModeObserver() {
  var observer = new MutationObserver(/* … */ updateZeroFills() /* … */);
  observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
}
```

The heatmap's **only** theme signal is the `.dark-mode` class on `<body>`. When
it mutates, `updateZeroFills()` re-reads `--heatmap-empty` and rewrites the
`fill` attribute on every zero-count cell and placeholder.

Why JS has to do it at all: cell fills are **SVG presentation attributes** set
to resolved colour strings, not `var()` references, so no stylesheet can update
them on a theme change.

**Consequence for WP-8, and it is a trap.** The stated plan is to retire
`global.css` and "the second write" together. Removing the `.dark-mode` write
silently breaks the heatmap's empty cells on theme toggle — nothing renders
wrong until a reader flips the theme with a grid on screen, and no gate watches
it. The observer must move to `data-theme` on `<html>` **in the same change**.
`global.css` is still dead; the class write is not.

## 2. Mobile heatmap is a different visualisation, not a reflow

Both documents are wrong here, differently. The handoff says "Four season strips
stack vertically on mobile." The code ships neither that nor a reflowed
calendar:

| | Desktop (`renderHeatmapDesktop`) | Mobile (`renderHeatmapMobile`) |
| --- | --- | --- |
| Shape | 7 rows, `numCols` from `mondayIndex(fromDate)` — calendar-aligned weeks | `rows = ceil(totalDays / columns)`, a continuous run of days |
| Weekday alignment | Yes, Monday-first | **None** |
| Day labels | Mon / Wed / Fri | **None** |
| Month labels | Yes | **None** |
| Cell | 14px, 2px gap | sized to fit: target 22, clamped 18–28, 1px gap, 10–28 columns |
| `aria-label` | "Scrobble **heatmap** for …" | "Scrobble **activity strip** for …" |

The aria-label names it: a *strip*, not a heatmap. Losing weekday alignment is
the whole point — a phone cannot hold 53 columns, so the chart stops being a
calendar and becomes a density ribbon. That is a legitimate design decision and
it is recorded nowhere but in these two function bodies.

## 3. The colour mapping is logarithmic, and nothing says so

```js
function countToNorm(count, maxCount) {
  if (count <= 0 || maxCount <= 0) return 0;
  return Math.log10(count + 1) / Math.log10(maxCount + 1);
}
```

The handoff says cells are "coloured by the `rocket(t)` helper against the
seven-stop ramp" and stops there. The mapping from count to `t` is **log10**, so
one enormous day does not flatten every ordinary day to the dark end. For a
data-density ramp that is the single most consequential decision in the chart,
and it is absent from the design system.

## 4. Three mechanical SVG constraints the design system must carry

All three are the same root cause — **an SVG presentation attribute does not
resolve a CSS custom property** — and each cost a separate workaround:

1. **`LABEL_FONT_STACK` is hardcoded**, with the reason in the comment: "Named
   here rather than read from `var(--font-mono-narrow)`, because these land on
   an SVG presentation attribute, where a custom property does not resolve."
2. **`zeroFill()`** reads `--heatmap-empty` through `getComputedStyle` before
   assigning, so the downloaded grid carries the colour without the stylesheet.
3. **`resolvedColour(token)`** paints a probe `<div>` and reads `color` back,
   because `getPropertyValue` can hand back unresolved `var(--other)` text —
   exactly the `--heatmap-surface: var(--ss-surface-sunken)` indirection.

A fourth, related: **the Adobe kit does not load inside a serialized SVG**, so
`gridAsImage()` pins the clone's label font to a plain monospace stack. Leaving
the kit families there would let the renderer pick any fallback it liked, and
the saved file would differ per machine.

## 5. Two export architectures, and the export honours a rule the page breaks

`saveHeatmapImage()` draws a canvas **by hand**, and says why:

> The results page uses html2canvas for the same job and carries about ninety
> lines of workarounds for colours it renders wrongly; the heatmap is an SVG on
> a flat background, so none of that is needed and no library is loaded onto a
> migrated page.

So there are two export paths with different costs, and the design system
describes neither. Details worth recording: `EXPORT_SCALE = 2` for high-density
screens; a measured responsive header that wraps the KPI columns 4 → 2 → 1
("two keeps a four-item row square rather than leaving one orphan"); the legend
sits beside the KPIs "when there is honestly room" and takes its own row
otherwise; and a recorded bug — a flat header height of 150 was shorter than its
content (KPI row ends at 166, legend at 154) so the grid painted over both.

And the type split is the opposite way round from the page:

```js
const KPI_LABEL_FONT = '10px "input-mono-narrow", "input-mono", monospace';
const KPI_VALUE_FONT = '24px "gotham", sans-serif';
```

**The export uses Gotham for figures** — honouring the Role Segregation Rule —
while the Results page deliberately uses the serif. Canvas text can use the kit
"because it draws in this document where they are already loaded." So the rule
is alive in one render target and intentionally set aside in another. That is
worth stating plainly in the rewrite rather than leaving the rule absolute.

One self-documented deviation: "the design asks for the desktop 53x7 grid even
when the reader is on a phone. This saves whatever layout is on screen."

## 6. The ramp's single-source rule is explicit

`initPreviewRamp()` confirms what I inferred about `--rocket-*`:

> It reads `ROCKET_STOPS` through the same helper the legend uses, so the two
> cannot drift. **The CSS deliberately does not carry the seven stops: one copy
> of the ramp, and this file owns it.**

So the absence of `--rocket-0..6` is a deliberate architectural decision, not an
omission. The design system should state it as a rule.

## 7. Loading is richer than "three stats in a row"

- **Up to five stats, revealed progressively.** Each `.loading-stat` stays
  `.hidden` until its value arrives and the container reveals when any has one:
  scrobbles, pages fetched, albums passing filter, Spotify matched, plus a cache
  line ("N albums loaded from cache") and a `partial_data_warning` slot. The
  handoff specifies a fixed row of three.
- **The progress bar has an error state** — `progressBar.classList.add('is-error')`.
- **The bar is a `scaleX()` transform**, not a width, and a phase change resets
  it instantly: `transition: none` → `scaleX(0)` → double `requestAnimationFrame`
  → restore → animate to the new value. Without that, a new phase would animate
  *backwards* from the old phase's fill.
- **Phase label format**: `PHASE · UNIT current / total`, uppercased, U+00B7
  separator. The handoff's copy rule ("Fetching scrobbles · page 31 of 45") is
  implemented as `FETCHING SCROBBLES · PAGE 31 / 45` — uppercase, and a slash
  rather than "of".
- **A deliberate three-second reading delay** before redirecting, with an
  explanation in the details line ("Opening your results…"). The comment calls
  it out as intentional: "retain the three-second reading delay".
- **Errors name the failing service** — "Source: Last.fm" / "Source: Spotify" —
  and the retry button appears only when the payload says `retryable`, changing
  to "Retrying…" on click. Every string follows the "say why, then say the fix"
  rule: "The progress service could not be reached." / "Try the connection again
  or return home."
- `aria-valuenow/min/max` **and `aria-valuetext`** carrying the human label, on
  both the track and the bar.

## 8. Artist Spotlight: the app's only auto-advancing element

- **7,000ms rotation**, paused while `document.hidden`.
- **`prefers-reduced-motion` stops rotation entirely** and skips the cross-fade,
  holding the first artist still.
- **The cross-fade dips to opacity 0.15, not 0**, so the card never goes blank —
  then swaps after 150ms and returns to 1.
- **A coupling mismatch**: `.spotlight-card-content` has
  `transition: opacity 0.25s ease-out` in CSS, but the JS swaps at 150ms, so the
  fade-out is cut off mid-transition. Same class of problem as the 140ms pair —
  two files holding two halves of one timing with no comment linking them.
- **Rank reads `01 / 12`**, zero-padded — the same archival numbering as the
  hero's `§ 01`.
- Text-only fallback via `.spotlight-no-image` when no portrait resolves; alt
  text "Photograph of {name}"; link label "View {name} on Spotify (opens in new
  tab)".

## 9. A house pattern worth naming

The same stale-response guard appears **four times** in four shapes:
`validationGeneration` (index.js), `state.imageRevision` (results-spotlight.js),
`latestAppliedPollSeq` (loading.js), and a name-equality recheck before and
after `await` (unmatched.js and the spotlight hydrator). Every async UI update
in this app discards a response that has been superseded. That is a genuine
convention, and a design system that documents component behaviour should say
so, because the failure it prevents — a late response painting the wrong
artist's portrait, or an old username's verdict — is invisible in review.

## 10. One stale code comment

`renderHeadline()` opens: *"A year of <name>, not the old possessive range
sentence."* The function then builds exactly a possessive:

```js
nameSpan.textContent = username;
resultHeadline.appendChild(document.createTextNode('’s last 365 days of scrobbling'));
```

So the rendered headline is `{username}'s last 365 days of scrobbling` — a third
variant, matching neither the handoff's "A year of listening, one grid" nor
RECONCILIATION's "Your last 365 days, one grid" (that one is the *index hero*,
which does match). The comment describes a state the code left behind. Minor,
but it is the kind of comment a later agent will trust.

## What is now verified, and what is not

Every page stylesheet, every template, and all nine JS files have been read.
The heatmap and loading sections of the rewrite can be treated as verified.

Still unread: `app.py` and the `scrobblescope/` package. They own the KPI
payloads, the progress phase labels and units, the `page_navigation` context
variable, and `/api/artist_spotlight` — so some of the *copy* the design system
specifies is authored server-side and none of it has been checked against the
content rules. That is a smaller and different gap than this one was, and worth
closing only if the rewrite means to make claims about copy.
