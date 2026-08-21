# ScrobbleScope Design System

ScrobbleScope is a Flask + Jinja2 web app that reads your Last.fm scrobbles and answers two questions: **what did I actually play this year**, and **what did my listening look like day by day**. It filters top albums by release date (year, previous year, decade, custom year, or no filter), ranks them by play count or real listening time, applies play/track thresholds, explains every album that *didn't* match, and exports results as CSV or JPEG. A second mode renders a 365-day listening heatmap using seaborn's `rocket_r` colour scale.

This design system captures the product's **target** visual language: the warm palette and editorial type that the shipped heatmap already uses, promoted to the whole app. The current production UI is Bootstrap 5 with cool greys; the settled direction (see `CLAUDE.md` in the source zip) is Tailwind + DaisyUI, still server-rendered — not React. The React components here are a **specification and prototyping kit**, not the shipping implementation.

## Sources

| Source | What was read |
| --- | --- |
| `github.com/pterw/ScrobbleScope` (branch `main`) | `templates/*.html`, `static/css/*.css`, `static/js/heatmap.js`, `templates/inline/*.svg`, `templates/base.html` — the ground truth for current markup, tokens, geometry and the rocket_r stops |
| `uploads/UI Design Conceptions/ScrobbleScope UI Audit v3.html` | A prior UI/UX audit with mockups; source of the proposed warm palette, type system and screen redesigns |
| `uploads/UI Design Conceptions/CLAUDE.md` | Non-negotiable assets and settled stack decisions |
| `uploads/*.svg` | Wordmark, inline wordmark, pinwheel, favicon |

Explore the repository directly for anything not covered here — the templates and per-page CSS are small and readable, and they remain the authority on current behaviour: **https://github.com/pterw/ScrobbleScope**

Two products exist in principle (the web app and its social/link-preview surface), but only one has real screens, so there is **one UI kit**: `ui_kits/scrobblescope-web/`.

## Content fundamentals

**Voice.** Direct, second person, slightly opinionated about music. The product is made by someone who builds AOTY lists and assumes you do too. It explains mechanics without apologising for them.

- **You, not we.** "Albums you listened to in 2025", "your filter criteria", "Lower to ≥5 plays to include 14". The app never says "we found" — the shipped copy slips into "We couldn't find any…"; prefer "No 2025 releases cleared your thresholds."
- **Sentence case everywhere.** "Search albums", "Export CSV", "Quick view unmatched" — not Title Case. The shipped Bootstrap build uses Title Case labels ("Export to CSV", "Number of Albums to Display"); those are legacy, and the design system standardises on sentence case.
- **Labels are nouns, buttons are verbs.** "Listening year" / "Search albums". Never "Submit", never "OK".
- **Numbers are exact and mono.** `247`, `18h 42m`, `≥10 plays`. Use the `≥` glyph, not "at least".
- **Say why, then say the fix.** The unmatched page is the tone benchmark: every group names the reason in plain language ("Played, but under ≥10 plays or ≥3 unique tracks") and then states the single change that would include them ("Lower to ≥5 plays to include 14 of these"). Never "loosen your filters".
- **No exclamation marks in new copy.** The shipped "Filter Your Album Scrobbles!" and "Welcome to ScrobbleScope!" are the old register; the new headline voice is declarative — "Your top albums, *any year or decade.*"
- **Name the capability, not the internal term.** The play/track minimums are "what counts as listened" in the UI, never "thresholds"; the release filter says "any year or decade", not "release scope".
- **No emoji.** None appear anywhere in the product, and none should be added.
- **Micro-copy is mono and lowercase.** Field hints ("public profile", "2002–2026") sit right-aligned in the label row in Input Mono Narrow, lowercase.
- **Loading copy states progress, not encouragement.** "Fetching scrobbles · page 31 of 45", not "Hang tight, almost there".

## Visual foundations

**The move.** Cool developer-tool greys (`#f8f9fa`, `#121212`, `#333`) → warm off-whites and inky-purple darks. The heatmap frame (`#faf8f3` light / `#181520` dark, 14px radius) shipped first and is the reference for everything else. Purple `#6a4baf` is the one fixed brand colour and does not change.

- **Colour.** Light: page `#faf8f3`, sunken `#f0ebe0`, card `#ffffff`, ink `#1a1820`, hairline `#e5dfd1`. Dark: page `#0e0c12`, sunken `#1a1622`, card `#181520`, text `#f1ede4`, hairline `#2a2434`, purple lifts to `#b39dde` for contrast. Status colours exist but are used as 3px rules and mono kickers, never as full-bleed tinted cards. Data colour comes from one place only: the seven-stop `rocket_r` ramp.
- **Type.** Five roles, one family each, all served from **Adobe Fonts kit `rwy8ghw`** (`<link rel="stylesheet" href="https://use.typekit.net/rwy8ghw.css">`). Nothing is self-hosted; the product ships no font binaries. **Akzidenz-Grotesk Next Pro** (`akzidenz-grotesk-next-pro`) for all UI chrome and body. **Instrument Serif** (`instrument-serif`) for display *words* only, never under 22px. **Gotham** Book (`gotham`) for display *numbers* only, 18px and up — its geometric lining figures are the closest kin to the wordmark, and it is never used for chrome or at Bold. **Input Mono** (`input-mono`) for form inputs and tabular numbers. **Input Mono Narrow** (`input-mono-narrow`) for letterspaced caps — eyebrows, pills, hints, keys; full-width Input is too wide at 9–10px and overflows label rows. The signature move: mono uppercase label above a Gotham numeral. **Critical constraint: no family in the kit ships a 500 or a 600.** The weight scale is 300 / 400 / 700 only; any 500 or 600 in code produces a browser-synthesized fake. `akzidenz-grotesk-next` (classic) and `akzidenz-grotesk-next-conden` are also in the kit — the classic has no usable text weight (200 roman/italic + 800 italic only) and the condensed is retained purely as a licensing hedge in case Adobe rotates families out. Neither is used.
- **Spacing.** 4px base, seven steps: 4 / 8 / 12 / 16 / 24 / 32 / 48. Form fields 12px apart, card padding 16px mobile / 24px desktop, page gutter 18px mobile / 34px desktop.
- **Corner radii.** 4px cover art, 8px inputs, 10px stat strips and solid buttons, 14px cards and the heatmap frame, 999px pills. Nothing else.
- **Cards.** A warm surface, a 1px hairline border, 14px radius, **no drop shadow**. Cards are defined by their edge, not their elevation. Nested panels switch to the sunken surface rather than stacking borders.
- **Buttons.** At most one solid action per screen, filled with the brand purple in both themes (white text on
  light, near-black on dark). Solid ink was tried on light and read as too heavy against the cream. Everything
  else is a hairline-bordered card button or a ghost. Weight is **400, never 700** — bold button labels read as
  stapled on. Labels are `white-space: nowrap`. Where several actions sit together in a toolbar (Export CSV /
  Save image / New search) they are all peers in the hairline treatment: a solid brand fill on one of three
  equals reads as an unearned hierarchy.
- **Shadows.** Almost absent. Three exist: `--shadow-chip` (the raised selected segment of a segmented control), `--shadow-float` (toast, tooltip), `--shadow-modal`. No inner shadows anywhere.
- **Backgrounds.** Flat warm colour. No gradients, no textures, no hero photography, no illustration. The only gradients in the system are the rocket_r ramp and the muted two-tone washes standing in for missing album art. Album cover art is the *only* imagery — real, square, 38–44px in lists, 4px radius. As it should be. 
- **Transparency & blur.** Used twice: sticky bars (`color-mix` of the page colour + `blur(8px)`) and the modal scrim. Never on cards, never for "glass" decoration.
- **Borders.** One weight — 1px, `--border-default`. Dashed 1px marks a disclosure boundary (the threshold row). Divider lines between list rows replace zebra striping.
- **Animation.** Quiet. 200ms colour/border on hover, 300ms theme swap, 500ms content fade-in with a 20px rise, 2s wordmark fade on load. No bounces, no springs, no parallax. Two deliberate exceptions, both fixed assets: the **pinwheel** (2.5s, 1080° rotation with a 5.4-unit blade expansion) and the **five logo bars**. The bars are driven by **CSS keyframes, not SMIL** — `<animate>` does not survive asset storage, so `Wordmark` fetches the SVG, strips any `<animate>`/`<animateTransform>`, injects it inline, and `tokens/base.css` animates it: `scaleY(1)` → `scaleY(1.10)` on durations 1.6 / 1.7 / 1.9 / 2.1 / 2.3s, intentionally never in sync. Two non-obvious requirements: the selector is capped at `#horizontal_bars path:nth-of-type(-n+5)` so it can never reach a letterform path, and the transform must use `transform-box: view-box; transform-origin: 0 63.5px` — **not** `fill-box`. Each bar is a pure vertical line, so its fill box is zero-width and excludes the stroke; `fill-box` resolves against a degenerate box and the bars drift instead of scaling. All five share the baseline y=63.5. **Letterforms never move.**
- **Hover.** Opacity 0.86 on buttons; border and text shift to purple on pills and inputs. Never a size change, never a shadow bloom.
- **Press.** Colour only — no shrink transform.
- **Focus.** 2px solid `--accent` ring, 2px offset, on every interactive element.
- **Layout.** Content is centred and capped: 1180px for results and unmatched, 1040px for the heatmap, \~380–460px for the form column. The index page is a two-column split on desktop (editorial left, form right, sunken background on the form side) and stacks on mobile. Sticky elements: the results sidebar (desktop), the export bar (mobile).
- **Imagery vibe.** Warm, low-saturation, cream-and-ink. The only saturated colours in the product are the brand purple and the rocket ramp's oranges and golds.

## Iconography

**There is essentially no icon system, and that is deliberate — do not invent one.** Findings from the codebase:

- The shipped UI is text-first. Buttons carry words ("Export to CSV", "Retry Now"), not glyphs.
- Exactly one inline SVG icon exists in the templates: the exclamation-circle on `error.html` (a Bootstrap-Icons path, hand-inlined, 64px, `currentColor`).
- Everything else that looks like an icon is a Unicode character or a CSS shape: `↑ Top` (`&#8593;`) for back-to-top, `×` for modal close, `?` in a 1.1rem circle for the field tooltips, `−`/`+` for steppers, a two-triangle CSS gradient for the select chevron, and a small purple square as the mode-tab mark.
- No icon font, no sprite sheet, no SVG icon directory, no emoji — anywhere.

**Rules for new work.** Prefer a word. If a glyph is unavoidable, use the Unicode characters already in use above. If a real icon set ever becomes necessary, **Lucide** (1.5px stroke, 24px grid, CDN: `https://unpkg.com/lucide-static`) is the closest match to the geometric, thin-stroke wordmark — but note clearly that this would be a **new addition, not a recreation**; nothing in the current product uses it.

Brand SVGs that *do* ship, all in `assets/`: `scrobble_scope_inline.svg` (theme-reactive: text `currentColor`, bars `var(--bars-color)`), `scrobble_scope_light.svg` / `scrobble_scope_dark.svg` (baked ink + bar colours), `scrobblescope_pinwheel.svg` (SMIL, reads `--bars-color`), `favicon.svg`, `favicon.ico`, `favicon-32x32.png`, `social-card.png` (1200×630 link preview). Reference screenshots of the live app are in `assets/screens/`.

> **Asset caveat:** the uploaded copies of the wordmark and pinwheel had their `<style>` blocks and SMIL stripped in transit. Paint attributes and the bar/blade animations were restored from the repository (`templates/inline/`). If you re-import these assets, take them from GitHub raw, not from a copy.

## Components

Grounded in the actual inventory of the Flask templates and the audit's proposed screens.

**Actions** — `Button` **Layout** — `Card`, `SectionHeading`, `Disclosure` **Forms** — `Field`, `Input`, `Select`, `PillGroup`, `SegmentedControl`, `Stepper`, `Switch` **Navigation & brand** — `Wordmark`, `WordmarkLockup`, `ModeTabs`, `ThemeToggle` **Data** — `AlbumRow`, `StatBlock`, `Tag`, `UnmatchedGroup` **Feedback** — `Alert`, `Toast`, `ToastStack`, `Modal`, `ProgressBar`, `Pinwheel` **Heatmap** — `HeatmapFrame`, `HeatmapGrid`, `HeatmapLegend`, plus the `rocket(t)` colour helper

Each directory holds `<Name>.jsx`, `<Name>.d.ts`, `<Name>.prompt.md` and one `@dsCard` HTML.

**Intentional additions** (not one-to-one with shipped markup, and why):

- `SegmentedControl` and `Stepper` — the audit replaces the "Sort by" select and the two threshold selects with these; they exist in the proposed design, not in the current Bootstrap build.
- `WordmarkLockup` — needed for a compact app header; the shipped app only ever renders the full mark.
- `Tag` — consolidates three shipped patterns (release badge, filter summary text, loading parameter list) into one chip.
- `ModeTabs` — a restyle of the shipped `.mode-pill` bar, not a new concept.

## Files

- `styles.css` — the single entry point consumers link. Imports only.
- `tokens/` — `fonts`, `colors`, `typography`, `spacing`, `radius`, `elevation`, `motion`, `heatmap`, `base`.
- `components/` — `actions/`, `layout/`, `forms/`, `navigation/`, `data/`, `feedback/`, `heatmap/`.
- `guidelines/` — foundation specimen cards, plus `audit-review.md` (a second-pass critique of the uploaded UI audit: what to keep, what reads as generic AI-generated UI, and what to fix).
- `ui_kits/scrobblescope-web/` — click-through recreation of all five screens in both themes.
- `assets/` — logos, pinwheel, favicons, social card, reference screenshots.
- `templates/` — starting-point templates consuming projects can copy.
- `design_handoff_scrobblescope_frontend/` — implementation package for Claude Code: a self-sufficient README plus copies of the tokens, components and click-through prototypes.
- `SKILL.md` — entry point when this system is used as an Agent Skill.
- `github.md` — source repository association and sync record.
