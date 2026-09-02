# Handoff: ScrobbleScope front-end

## Overview

ScrobbleScope is a Flask + Jinja2 web app that reads a user's Last.fm scrobbles and answers two questions: **what did I actually play this year**, and **what did my listening look like day by day**.

Mode one filters top albums by release date (same year, previous year, decade, custom year, or no filter), ranks them by play count or real listening time, applies play/track minimums, explains every album that *didn't* match, and exports CSV or JPEG. Mode two renders a 365-day listening heatmap on seaborn's `rocket_r` scale.

This package is the **target visual language** for the whole app: the warm palette and editorial type that the shipped heatmap already used, promoted everywhere. Production today is Bootstrap 5 with cool greys. This replaces that.

## About the design files

**The files in this bundle are design references, not production code.** They are HTML/React prototypes that demonstrate intended look, behaviour and exact values. Do not copy the JSX into the app.

The task is to **recreate these designs in ScrobbleScope's existing environment**: Flask + Jinja2 templates, server-rendered, styled with **Tailwind + DaisyUI**. That stack decision is settled — see `CLAUDE.md` in the source repo. **This is not a React app and should not become one.** The React components here exist because they were the fastest way to specify and prototype the system precisely; treat each one as a spec for a Jinja partial or macro plus Tailwind classes.

Repo: **https://github.com/pterw/ScrobbleScope** (branch `main`). The current templates and per-page CSS are small and readable and remain the authority on existing behaviour.

## Fidelity

**High-fidelity.** Colours, typography, spacing, radii and interaction states are final and exact. Recreate them precisely. Every value you need is in `tokens/` — port that directory into the Tailwind theme rather than transcribing values by hand into class names.

The one deliberately unfinished area is imagery: album cover art is represented by muted two-tone washes. Real cover art from the Last.fm API replaces those.

---

## Design tokens

Port `tokens/*.css` as CSS custom properties and reference them from the Tailwind config. They are already plain CSS with a `.dark` scope — they do not need translating.

### Colour — light

| Token | Value | Use |
| --- | --- | --- |
| `--surface-page` | `#faf8f3` | Page background |
| `--surface-sunken` | `#f0ebe0` | Form column, nested panels |
| `--surface-card` | `#ffffff` | Cards, secondary buttons |
| `--text-strong` | `#1a1820` | Headings, values, labels |
| `--text-body` | `#4a4456` | Paragraphs |
| `--text-muted` | `#6f6a7a` | Hints, eyebrows, meta |
| `--border-default` | `#e5dfd1` | Every hairline |
| `--accent` / `--text-accent` | `#6a4baf` | The one fixed brand colour |
| `--accent-soft` | `#efe9fa` | Accent tint |
| `--accent-contrast` | `#ffffff` | Text on accent fill |

### Colour — dark (`.dark` on `<html>`)

| Token | Value |
| --- | --- |
| `--surface-page` | `#0e0c12` |
| `--surface-sunken` | `#1a1622` |
| `--surface-card` | `#181520` |
| `--text-strong` | `#f1ede4` |
| `--text-body` | `#c5bfb1` |
| `--text-muted` | `#908a9a` |
| `--border-default` | `#2a2434` |
| `--accent` / `--text-accent` | `#b39dde` |
| `--accent-soft` | `#2a1f44` |
| `--accent-contrast` | `#0e0c12` |

Purple `#6a4baf` is the fixed brand colour and lifts to `#b39dde` in dark for contrast. Status colours (`--ss-good` `#2f7a4a`/`#6fcf97`, `--ss-warn` `#b35a1f`/`#e0a458`, `--ss-bad` `#b03434`/`#e07070`) are used as 3px rules and mono kickers, never as full-bleed tinted cards.

**The theme class goes on `<html>`, not an inner wrapper** — otherwise the page shell stays light while the content flips.

### Heatmap — the `rocket_r` ramp

Seven stops, dark to light. **Never re-order, never re-tint.** The grid, the legend and the exported JPEG all read from these.

`--rocket-0` `#03051a` · `--rocket-1` `#2a0f4e` · `--rocket-2` `#6a176e` · `--rocket-3` `#a62c5c` · `--rocket-4` `#d44e41` · `--rocket-5` `#f0903a` · `--rocket-6` `#f9d576`

| Token | Light | Dark |
| --- | --- | --- |
| `--heatmap-empty` | `#e8e2d6` | `#262230` |
| `--heatmap-surface` | `#faf8f3` | `#181520` |

Empty cells are warmed off pure grey in light so they sit on cream, and tinted to the surface hue in dark — a neutral grey there reads warm against the purple-black and picks up a cast from the orange end of the ramp. Cell radius 2px; gap 2px desktop, 1px mobile.

### Type

All from **Adobe Fonts kit `rwy8ghw`**. Add to `<head>`:

```html
<link rel="stylesheet" href="https://use.typekit.net/rwy8ghw.css">
```

| Token | Family | Role |
| --- | --- | --- |
| `--font-sans` | `akzidenz-grotesk-next-pro` | All UI chrome, labels, body |
| `--font-serif` | `instrument-serif` | Display **words** only, 22px+ |
| `--font-figure` | `gotham` | Display **numbers** only, 18px+, Book only |
| `--font-mono` | `input-mono` | Form inputs, tabular numbers |
| `--font-mono-narrow` | `input-mono-narrow` | Letterspaced caps: eyebrows, pills, hints, keys |

**Read this before writing any font-weight.** No family in this kit ships a 500 or a 600. The scale is **300 / 400 / 700 only**. A `font-weight: 500` produces a browser-synthesized fake that looks subtly wrong — and Tailwind's `font-medium` is exactly that. Hierarchy comes from size, colour and letterspacing, not from a medium weight.

Two more rules that are easy to get wrong:

- **Gotham gets the numbers, Instrument Serif gets the words.** They never compete for the same slot. Gotham is never used for chrome and never at Bold — geometric numerals blob at 700.
- **Input Mono Narrow, not Input Mono, for anything letterspaced at 9–11px.** Full-width Input is wide enough to push a `nowrap` field hint into the label and clip it. This actually happened; it is the single most likely regression.

Sizes: display 42 / 30 / 22px, leading 1.05, tracking −0.01em. Body 16 / 14 / 12px, leading 1.5, label 11.5px. Mono data 13 / 11 / 10 / 9.5px, eyebrow tracking 0.12–0.14em.

### Spacing, radius, elevation, motion

- **Spacing** — 4px base, seven steps, nothing between: 4 / 8 / 12 / 16 / 24 / 32 / 48. Card padding 16px mobile, 24px desktop. Page gutter 18px mobile, 34px desktop. Form fields 12px apart.
- **Radius** — four values: 4px cover art and tiny tags, 8px inputs and small buttons, 10px stat strips and submit buttons, 14px cards and the heatmap frame, 999px pills. Nothing else.
- **Elevation** — borders do the work. Cards are a 1px `--border-default` line on a warm surface with **no drop shadow**. Only three shadows exist: `--shadow-chip` `0 1px 3px rgba(0,0,0,.06)` (selected segment), `--shadow-float` `0 2px 8px rgba(0,0,0,.15)` (toast, tooltip), `--shadow-modal` `0 24px 60px -24px rgba(20,18,30,.4)`. Dark raises each to `.4`/`.4`/`.7`. Scrim `rgba(14,12,18,.5)` light, `rgba(0,0,0,.62)` dark. Sticky blur `blur(8px)`.
- **Motion** — hover 200ms, theme swap 300ms, content enter 500ms with a 20px rise, wordmark fade 2000ms, pinwheel cycle 2.5s. Easing `ease` standard, `cubic-bezier(.22,.61,.36,1)` for out. All durations collapse to 0ms under `prefers-reduced-motion`. No bounces, no springs, no parallax.

---

## Screens

Five screens, all in `ui_kits/scrobblescope-web/`. Open `index.html` and use the header pills to move between them; the theme toggle flips light/dark. The pills are prototype scaffolding — **do not build them**.

### 1. Index — `IndexScreen.jsx`

**Purpose:** enter a username, choose a mode, set filters, submit.

**Layout:** two-column grid on desktop, `1.1fr 1fr`, both columns top-anchored with fixed padding so nothing re-centres when the form grows or the browser zooms. Left column 56px padding all round, editorial. Right column sunken background, 1px left border, 52px/44px/56px padding, form capped at 380px. Stacks to one column under 860px.

**Left column, in order:** wordmark (lockup — the no-tagline variant); mono eyebrow reflecting the mode ("Album filtering" / "Listening heatmap"); serif h1 42px with one italic purple accent clause; 14px body paragraph capped at 38ch; a row of three mono capability marks each prefixed with a purple `→`.

The wordmark spans the column width so its left, right and top insets all equal the 56px padding, **capped at 560px** — uncapped it grows with the viewport until it dwarfs the h1. Its wrapper needs an explicit `height: auto`; a fixed height on the wrapper with a fluid SVG inside makes the mark overflow its box and the h1 slides underneath it.

**Right column:** mode tabs (Top albums / Heatmap, the Heatmap tab marked with `--rocket-5` orange); then a 14px-radius card at 18px padding containing, in order — Last.fm username (hint "public profile", green check when >2 chars); Listening year (hint "2002–2026", help "Only plays inside this calendar year are counted."); Album release filter select (Same as listening year / Previous year / Choose decade / Pick specific year / All years); conditionally a centred decade pill group (2020s→1950s, pre-1970s disabled) or a release-year input; Rank by segmented control (Play count / Play time); Show select (All results / Top 10 / 25 / 50 / 100); a dashed-top disclosure "What counts as listened" summarising `≥N plays · ≥N tracks` and opening two stepper rows; then the one solid purple submit, full width, trailing `→`. Below the card, four outline tags echoing the active filters.

In heatmap mode the card collapses to a single line — "The heatmap always covers the last 365 days. No other settings." — and the tags are replaced by a bordered preview panel listing what you'll get, closed by an 8px `rocket_r` gradient bar.

**Copy, exactly:** h1 album mode "Your top albums, *any year or decade.*" / heatmap mode "A year of listening, *one grid.*" Body: "Rank a single year, a whole decade, or your entire history — by play count or by the hours you actually spent listening. Built for AOTY lists with the nuance the official charts never give you." Submit: "Search albums" / "Generate heatmap".

### 2. Loading — `LoadingScreen.jsx`

**Purpose:** hold attention during a multi-page Last.fm fetch.

Centred column, 64px top padding. The **pinwheel** (built from the S of the wordmark, 2.5s, 1080° rotation with a 5.4-unit blade expansion, reads `--bars-color`); a mono uppercase phase line; a progress bar; three stats in a row with mono uppercase labels above Gotham 22px figures; a dashed-top row of mono parameter tags.

Progress copy states progress, never encouragement: "Fetching scrobbles · page 31 of 45", not "Hang tight". Exactly one progress signal at a time — do not run a bar and a spinner and a percentage together.

### 3. Results — `ResultsScreen.jsx`

**Purpose:** the ranked leaderboard.

Max width 1180px, 32px/34px padding. A `SectionHeading` (mono eyebrow carrying live state "Top albums · 2025 · play count", serif h2 "What *pterw* had on repeat.", 13px description with the exact counts, and a right-aligned action group: Export CSV / Save image / New search — **three hairline peers, no solid fill**). Then a `236px 1fr` grid: sticky sidebar of three stat blocks, filter tags, and two full-width unmatched buttons; main column of album rows.

**Album row:** rank number, 38–44px cover at 4px radius, album title 12px `--text-strong` at weight 400 with artist in muted 10px, then a right-aligned block of the Gotham/Input Mono value over a mono release date. Rows are separated by 1px divider lines — **no zebra striping**.

Note the headline construction: `SectionHeading` takes `title`, `accent` and `titleAfter` so the italic purple accent can sit mid-sentence. The accent is only ever the user's own data — their username. Never the year: the year is the filter, so a hardcoded one becomes a lie the moment someone picks 2007.

### 4. Heatmap — `HeatmapScreen.jsx`

**Purpose:** 365 days of scrobbles as a grid.

Max width 1100px. Frame at `--heatmap-surface` with a 14px radius. Cells 2px radius, 2px gap desktop / 1px mobile, coloured by the `rocket(t)` helper against the seven-stop ramp; zero-scrobble days take `--heatmap-empty`. Four season strips stack vertically on mobile. Stat blocks show total, daily average, best day and current streak. A legend bar carries the ramp with min/max labels. Hovering a day reveals what was played.

### 5. Unmatched — `UnmatchedScreen.jsx`

**Purpose:** explain every album that was excluded, and how to include it.

Max width 1180px, three-column grid of `UnmatchedGroup` cards, one column on mobile. Each card: reason at 12px weight 700, the count as a Gotham 22px figure in accent purple, a 10.5px muted explanation, then rows of album · artist with a mono note, then a single **purple mono uppercase fix line at 9px, held to one line** with the full string on hover.

**This screen is the tone benchmark for the whole product.** Every group names the reason in plain language ("Played, but under ≥10 plays or ≥3 unique tracks") and then states the single change that would include them ("Lower to ≥5 plays to include 14 of these"). Never "loosen your filters".

---

## Interactions & behaviour

- **Navigation.** Index → loading → results *or* heatmap, by mode. Results → unmatched (and back). Any screen → index via the header wordmark.
- **Theme.** A two-segment pill toggle, top right. Toggles `.dark` on `<html>`. 300ms transition on background and colour.
- **Hover.** Opacity 0.86 on buttons; border and text shift to purple on pills and inputs. Never a size change, never a shadow bloom.
- **Press.** Colour only — no shrink transform.
- **Focus.** 2px solid `--accent` ring at 2px offset on every interactive element. Non-negotiable.
- **Validation.** Username valid at >2 characters, shown as a green check inside the field. Year is numeric with `inputMode="numeric"`.
- **Disclosure.** The threshold panel is closed by default and marked by a dashed 1px top border. Its label is larger than its own summary, not smaller.
- **Loading.** One progress signal only.
- **Responsive.** Single breakpoint at 860px. Header 68px desktop / 60px mobile — fixed, so the wordmark sits at the same vertical position on every screen and does not shift between them. Mobile canvas reference is 390×844. **Touch targets never below 44px.**
- **Reduced motion.** All durations to 0ms; the wordmark bars stop.

## State

Server-rendered, so most of this is form state round-tripping through Flask. Client-side state is small:

| State | Values | Notes |
| --- | --- | --- |
| `theme` | `light` \| `dark` | Persist to `localStorage`; class on `<html>` |
| `mode` | `album` \| `heatmap` | Switches the whole form |
| `username` | string | Validated >2 chars |
| `year` | int | 2002–2026 |
| `scope` | `same` \| `previous` \| `decade` \| `custom` \| `all` | Reveals decade pills or a year input |
| `decade`, `releaseYear` | string | Conditional |
| `sort` | `playcount` \| `playtime` | |
| `limit` | `all` \| `10` \| `25` \| `50` \| `100` | |
| `minPlays`, `minTracks` | int (1–50, 1–10) | Steppers in the disclosure |
| `thresholdsOpen` | bool | Disclosure |
| progress / phase | int, string | Loading only, driven by the fetch |

## Assets

All in `assets/`. `scrobble_scope_lockup_{light,dark}.svg` (header and index mark, no tagline), `scrobble_scope_{light,dark}.svg` (full mark with tagline — for social and standalone use only, never above an h1 that says the same thing), `scrobble_scope_inline.svg` and `scrobble_scope_lockup_inline.svg` (theme-reactive: text `currentColor`, bars `var(--bars-color)`), `scrobblescope_pinwheel.svg`, `favicon.svg`, `favicon.ico`, `favicon-32x32.png`, `social-card.png` (1200×630).

**Wordmark animation — read this before touching the logo.** The five bars animate; **the letterforms never move**. SMIL does not survive asset storage, so the mark must be fetched and injected inline, with any `<animate>` / `<animateTransform>` stripped, and animated from CSS. Two non-obvious requirements, both in `tokens/base.css`:

1. Cap the selector at `#horizontal_bars path:nth-of-type(-n+5)`. Unqualified, it reaches any sixth-or-later path and animates letterforms.
2. Use `transform-box: view-box; transform-origin: 0 63.5px` — **not** `fill-box`. Each bar is a pure vertical line (`d="M15.13,32.45v31.05"`), so its fill box is zero-width and excludes the stroke; `fill-box` resolves against a degenerate box and the bars drift laterally instead of scaling. All five share the baseline y=63.5.

Keyframes: `scaleY(1)` → `scaleY(1.10)`, durations 1.6 / 1.7 / 1.9 / 2.1 / 2.3s with negative delays, intentionally never in sync.

> **Asset caveat:** if you re-import the wordmark or pinwheel, take them from GitHub raw (`templates/inline/`), not from a copy. Uploaded copies have had `<style>` blocks and SMIL stripped in transit.

## Iconography

**There is no icon system, and that is deliberate — do not invent one.** The shipped UI is text-first: buttons carry words, not glyphs. Exactly one inline SVG icon exists in the templates (the exclamation-circle on `error.html`). Everything else is a Unicode character or a CSS shape: `↑` back-to-top, `×` modal close, `?` in a circle for tooltips, `−`/`+` for steppers, a two-triangle CSS gradient for the select chevron, a small purple square as the mode-tab mark, `▲`/`▼` for the disclosure.

Prefer a word. If a glyph is unavoidable, reuse one of the above. No icon font, no sprite sheet, no emoji.

## Content rules

- **You, not we.** "Albums you listened to in 2025." Never "we found".
- **Sentence case everywhere.** "Search albums", "Export CSV" — the shipped Title Case labels are legacy.
- **Labels are nouns, buttons are verbs.** "Listening year" / "Search albums". Never "Submit", never "OK".
- **Numbers are exact and mono.** `247`, `18h 42m`, `≥10 plays`. Use the `≥` glyph, not "at least".
- **Say why, then say the fix.** See the unmatched screen.
- **No exclamation marks, no emoji.**
- **Name the capability, not the internal term.** "What counts as listened", never "thresholds". "Any year or decade", never "release scope".

## Files

This README lives at `design_handoff_scrobblescope_frontend/README.md` inside the ScrobbleScope design system. Every path below is **relative to the design system root** — the folder one level up from this file. Download the whole design system, not just this README; the sources are the other half of the handoff.

| Path | What it is |
| --- | --- |
| `styles.css` | Single entry point. Imports only. |
| `tokens/` | The real source of every value: `fonts`, `colors`, `typography`, `spacing`, `radius`, `elevation`, `motion`, `heatmap`, `base`. Port this directly into the Tailwind theme. |
| `components/` | 24 components as `<Name>.jsx` + `<Name>.d.ts` + `<Name>.prompt.md`, in `actions/ layout/ forms/ navigation/ data/ feedback/ heatmap/`. Specs, not shipping code. |
| `ui_kits/scrobblescope-web/` | Click-through prototype of all five screens in both themes. **Start here** — open `index.html` in a browser. `kit.css` holds the screen-level layout; the five `*Screen.jsx` files hold the composition. |
| `assets/` | Logos, pinwheel, favicons, social card, reference screenshots of the live app. |
| `guidelines/audit-review.md` | Second-pass critique of the original UI audit: what to keep, what reads as generic AI-generated UI, what to fix. Worth reading before adding anything new. |
| `guidelines/type-candidates.html` | Why this type stack, and the 400/700 weight constraint, shown at real UI sizes. |
| `readme.md` | The design system's own reference — voice, visual foundations, iconography, component rationale. Broader than this file; read both. |

**Do not copy this folder back into the design system as a self-contained bundle.** A duplicate of `components/` inside the project makes every component compile twice and collide on the same namespace.

## Known constraints, collected

The things most likely to bite, in one place:

1. **No 500 or 600 weight exists.** Tailwind's `font-medium` and `font-semibold` will synthesize fakes.
2. **Input Mono Narrow for small letterspaced caps**, not Input Mono. Wrong one clips field labels.
3. **`transform-box: view-box`** for the logo bars, never `fill-box`.
4. **Theme class on `<html>`**, not an inner div.
5. **Wordmark wrapper needs `height: auto`** if the SVG is fluid, and a `max-width` cap.
6. **The tagline lives inside the full logo art.** Use the lockup anywhere an h1 already states the proposition.
7. **`rocket_r` stops are fixed.** Never re-order or re-tint; the exported JPEG depends on them.
8. **Cards have no drop shadow.** Edge, not elevation.
9. **Mobile touch targets ≥44px**; the shipped build has inputs below that.
