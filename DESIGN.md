---
name: ScrobbleScope
description: An archival field notebook for public Last.fm listening histories and playtime analysis
colors:
  primary: "#6a4baf"
  primary-dark: "#b39dde"
  primary-content: "#faf8f3"
  primary-content-dark: "#0e0c12"
  accent-soft: "#efe9fa"
  accent-soft-dark: "#2a1f44"
  surface-page: "#faf7f0"
  surface-page-dark: "#0e0c12"
  surface-sunken: "#f0ebe0"
  surface-sunken-dark: "#1a1622"
  surface-card: "#f9f7f1"
  surface-card-dark: "#181520"
  text-strong: "#1a1820"
  text-strong-dark: "#f1ede4"
  text-body: "#4a4456"
  text-body-dark: "#c5bfb1"
  text-muted: "#6c6676"
  text-muted-dark: "#908a9a"
  border-default: "#e5dfd1"
  border-default-dark: "#2a2434"
  border-divider: "#8a867e"
  border-divider-dark: "#68646f"
  rocket-5: "#f0903a"
  heatmap-empty: "#c8bfad"
  heatmap-empty-dark: "#262230"
  good: "#2f7a4a"
  good-dark: "#6fcf97"
  bad: "#b03434"
  bad-dark: "#e07070"
typography:
  display:
    fontFamily: "degular, akzidenz-grotesk-next-pro, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "degular, akzidenz-grotesk-next-pro, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.15
  title:
    fontFamily: "akzidenz-grotesk-next-pro, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "akzidenz-grotesk-next-pro, ui-sans-serif, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "input-mono-narrow, input-mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.12em"
rounded:
  xs: "4px"
  sm: "8px"
  md: "10px"
  lg: "14px"
  full: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  xl: "1.5rem"
  "2xl": "2rem"
  "3xl": "3rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-content}"
    rounded: "{rounded.md}"
    padding: "0.625rem 1.25rem"
  button-secondary:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-strong}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 1rem"
  card:
    backgroundColor: "{colors.surface-card}"
    rounded: "{rounded.lg}"
    padding: "1.5rem"
  input-field:
    backgroundColor: "{colors.surface-card}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 0.75rem"
---

# Design System: ScrobbleScope

## Overview

**Creative North Star: "The Field Notebook for Scrobbles"**

ScrobbleScope is an archival field notebook for listening histories: analytical, structured, and precise, paired with literary editorial elegance. It approaches personal audio listening data not as generic marketing charts or gamified social widgets, but as a durable personal chronicle. The aesthetic balances the warmth and permanence of archival book design with the utilitarian rigor of a laboratory register.

The visual language rejects cool, clinical SaaS greys, loud neon gradients, bouncy physics animations, and vacuous decorative charts. Instead, it relies on warm parchment and deep ink grounds, razor-sharp hairlines, disciplined typographical role-assignment, and high-density tabular presentation. Brand presence is expressed through craft and typographic hierarchy rather than omnipresent logos or saturated accent washes.

**Key Characteristics:**
- **Warm Archival Ground:** Cream paper (`#faf7f0`) in light mode; deep purple-tinged obsidian (`#0e0c12`) in dark mode.
- **Strict Typographic Role Separation:** Degular for editorial words, geometric sans for structural chrome, tabular mono for parameters, and sculpted figures for numeric magnitude.
- **Hairline Architecture:** Structural containment achieved through 1px borders and tonal ground shifts rather than drop shadows.
- **Restrained Velvet Accent:** Royal velvet purple (`#6a4baf` / `#b39dde`) applied with extreme parsimony to direct attention.
- **Dense, Traceable Data:** Every metric, ranking, exclusion, and heatmap cell is readable, verifiable, and grounded in listener evidence.

## Colors

The palette draws from classic printing inks and warm archival paper, accented by a single velvet violet brand tint and the seven-stop scientific `rocket_r` density ramp.

### Primary
- **Velvet Royal Violet** (`#6a4baf` light / `#b39dde` dark): The singular brand accent. Reserved strictly for primary action buttons, focused input outlines, active navigation indicators, and the brand lockup bars.
- **Accent Soft** (`#efe9fa` light / `#2a1f44` dark): Gentle tint used for selected radio chips, active table row highlights, and subtle keyboard-focus halos.

### Neutral
- **Page Canvas** (`#faf7f0` light / `#0e0c12` dark): The root background canvas. Warmed off pure white to evoke rag paper; dark mode uses an obsidian ground with faint violet warmth rather than neutral computer grey.
- **Sunken Well** (`#f0ebe0` light / `#1a1622` dark): Ground for the index form column and secondary structural wells. Results panels and table use `--results-surface`, an equal sRGB mix of the page canvas and Sunken Well.
- **Card Surface** (`--ss-surface-card`): The general control surface for secondary actions. Results and Heatmap New search use the theme primary; the index uses its separate standout-card token.
- **Ink Strong** (`#1a1820` light / `#f1ede4` dark): Maximum-contrast text color for page titles, section headings, values, and primary labels.
- **Ink Body** (`#4a4456` light / `#c5bfb1` dark): Readable secondary text color for descriptive paragraphs and form field descriptions.
- **Ink Muted** (`#6c6676` light / `#908a9a` dark): Muted metadata, field hint copy, and timestamps; tuned to maintain 4.5:1 contrast against light and dark surfaces.
- **Hairline Border** (`#e5dfd1` light / `#2a2434` dark): The universal 1px structural dividing line for cards, inputs, and segment dividers.
- **Well Divider** (`#8a867e` light / `#68646f` dark): Higher-contrast vertical boundary separating the hero stage from the configuration well.

### Heatmap & Status
- **Heatmap Surface** (`--heatmap-surface`): The sunken well in light mode and the dark card tone in dark mode (owner refinement, 2026-09-10).
- **Rocket Stop 5 (Tangerine)** (`#f0903a`): The single warm accent drawn from seaborn's `rocket_r` ramp, used exclusively for the Heatmap mode indicator mark.
- **Heatmap Empty** (`#c8bfad` light / `#262230` dark): A warm neutral for zero-scrobble days, darker than the light frame so empty cells remain visible.
- **Timeline Surfaces** (`.heatmap-frame` only): Inside the chart frame the surface is `#f0ebe0` light / `#1f1b28` dark and the empty cell is `#c8bfad` light / `#2e2939` dark. They are declared on the frame, not in the `:root` or `[data-theme="dark"]` blocks, so the page background and every other screen keep the global tokens above.
- **Stream Layers**: Ten deterministic Rocket-derived colours distinguish featured artists by rank, from orange for the most played to purple for the least played. A neutral, theme-specific halo encloses the artist stack and compresses remaining plays to one quarter thickness. The Other listening control hides or shows it without moving the ribbons. Gridlines use `#e5dfd1` light / `#352e43` dark, labels use `#6c6676` light / `#908a9a` dark, and the focus outline uses `#6a4baf` light / `#b39dde` dark. The scrubber lists actual values as text.
- **Good / Success** (`#2f7a4a` light / `#6fcf97` dark): Forest pine for successful cache hits and validated inputs.
- **Bad / Error** (`#b03434` light / `#e07070` dark): Terracotta crimson for validation errors, private profile alerts, and failed jobs.

### Named Rules
**The Ink-and-Parchment Rule.** Surfaces must never default to cold `#ffffff` or browser-default dark `#121212`. Light mode is cream paper (`#faf7f0`); dark mode is deep obsidian ink (`#0e0c12`).
**The Accent Restraint Rule.** Primary violet is used on ≤10% of any screen surface. Its rarity is what gives it authority.
**The Status Hairline Rule.** Status colors appear exclusively as 3px indicator rules, icon strokes, or monospace kickers—never as saturated full-bleed background fills.

## Typography

Type is served by Adobe Fonts kit `rwy8ghw`. Five distinct families each perform a single, non-negotiable duty.

**Display Font:** `degular` (Degular, weight 600; `akzidenz-grotesk-next-pro`, then sans-serif, as fallback)
**UI Body & Chrome Font:** `akzidenz-grotesk-next-pro` (ui-sans-serif, system-ui fallback)
**Figure Font:** `gotham` (ui-sans-serif fallback, Book weight only)
**Code & Data Mono:** `input-mono` (ui-monospace, monospace fallback)
**Eyebrow & Label Mono:** `input-mono-narrow` ("input-mono", monospace fallback)

**Character:** The pairing of a confident geometric display sans with clinical Swiss grotesque and technical mono evokes a vintage monograph or catalog raisonee.

### Hierarchy
- **Display** (600 weight, `2rem` to `3rem`, line-height `1.05`, tracking `-0.015em`): Editorial hero phrases and main page banners (`degular`).
- **Headline** (600 weight, `1.5rem`, line-height `1.15`, tracking `-0.015em`): Section headings and mode titles (`degular`).
- **Title** (700 weight, `1rem`, line-height `1.25`): Card titles, form section labels, and modal headers (`akzidenz-grotesk-next-pro`).
- **Body** (400 weight, `1rem`, line-height `1.5`): Paragraph descriptions, documentation, and error explanations (`akzidenz-grotesk-next-pro`). Max measure 65–75ch.
- **Label / Eyebrow** (400 weight, `0.75rem` / 12px, line-height `1`, tracking `0.12em`, uppercase): Metadata tags, field labels, table headers, and status flags (`input-mono-narrow`).
- **Figure Numerals** (400 weight, `1.125rem` to `2.5rem`, tabular): Large quantitative readouts, play counts, and hours listened (`gotham`).

### Named Rules
**The Role Segregation Rule.** Gotham gets the numbers, Degular gets the words. They never compete for the same slot. Gotham is never used for UI chrome and never rendered at bold weight. One exception, the owner's choice (2026-10-22): the Results stat row sets all four values in Gotham Book with tabular figures, the Top Artist name included, so the row reads as one set of readouts.
**The No-Medium Rule.** The kit serves Akzidenz-Grotesk Next, Gotham and the monos at 300, 400, and 700 only, so never use `font-weight: 500` or `font-weight: 600` on them. The one exception is Degular, which the kit serves at 400 and 600 and which sets every heading at 600. Hierarchy is established through scale, contrast, case, and tracking.
**The Narrow Eyebrow Rule.** Anything letterspaced in uppercase between 9px and 12px must use `input-mono-narrow` to eliminate horizontal crowding and prevent field hint clipping.

## Layout

The spatial model uses a 4px baseline grid expressed strictly in `rem` units (at a 16px root: 4px = `0.25rem`, 8px = `0.5rem`, 12px = `0.75rem`, 16px = `1rem`, 24px = `1.5rem`, 32px = `2rem`, 48px = `3rem`).

### Desktop & Mobile Grid
- **Desktop Index Stage:** Asymmetric two-column composition (`3fr 4fr`). The left hero stage hosts the editorial title and brand lockup with generous padding (`3.5rem`). The right sunken well hosts the configuration form (capped at `27.5rem` base, positioned up to `2.5rem` above centre with header clearance).
- **Index Hero Strip:** Under the lede, each mode has a three-column strip: a display term with a line icon over one plain description, divided by hairline rules. One container query turns the strip into rows when its column is narrower than 26 term widths (`26em`). The strip is hidden below `860px`. The lede is capped at `48ch` and wrapped `pretty`.
- **Loading Stats:** Scrobbles and Pages fetched, then Cache hits and Albums to search (together the albums that passed the thresholds). Each rises into place on arrival. The finished page replaces itself (`location.replace`), so Back reaches the form.
- **Breakpoint Stacking:** Collapses to a single vertical column below `860px` (`53.75rem`).
- **Heatmap Stage:** Centered desktop frame capped by viewport width and height so the heatmap and stream scale together and help leave room for the pause control. Mobile uses its own compact layout.
- **Mobile Navigation:** At mobile viewports, destination pills organize in a single line across the header width with zero horizontal scrollbars, preserving the 44px minimum touch target height; the theme toggle sits below page content.
- **Document Header:** The navbar scrolls out of view with the document. The Results side rail remains sticky with its own top gap (owner screenshot clarification, 2026-09-10).

### Named Rules
**The Fixed Composition Rule.** The desktop index retains its window-derived scale as disclosures open. The complete form sits up to 2.5rem above centre. The lift gives way first and never takes the gap above the mode switch under 1.5rem; a form too tall for that falls back to plain centring. The floor under the header stays 0.25rem, and a window too short for the expanded form scrolls.
**The Relative Unit Rule.** All typographic and spacing dimensions are authored in `rem` so that user browser zoom and font-scaling preserve proportional layout harmony.

## Elevation & Depth

ScrobbleScope is flat by default. Depth is communicated tonally—by layering card surfaces over sunken wells on canvas paper—and structurally using 1px hairlines. Box shadows are never used for static decoration.

### Shadow Vocabulary
- **Chip Shadow** (`--ss-shadow-chip: 0 1px 3px rgb(0 0 0 / 0.06)` light, `0.4` dark): Subtle separation for selected segmented control pills.
- **Float Shadow** (`--ss-shadow-float: 0 2px 8px rgb(0 0 0 / 0.15)` light, `0.4` dark): Transient overlays, floating tooltips, and toast notifications.
- **Modal Shadow** (`0 24px 60px -24px rgb(20 18 30 / 0.4)` light, `0.7` dark): Dialog modals and full-viewport scrim overlays.

### Named Rules
**The Border-Over-Shadow Rule.** Surfaces rest flat. Structural separation is always achieved via `1px solid var(--border-default)` and background tonal contrast, never through drop shadows.
**The State-Only Elevation Rule.** Shadows appear only as dynamic responses to state (hover lift, active chip selection, or floating overlay).

## Shapes

Geometry is crisp, rational, and restrained. Rounded corners scale strictly according to container size.

### Corner Radius Scale
- **`xs` (4px):** Tiny pill tags and sub-metric chips. Provider artwork (album covers, artist photos and their placeholders) follows Spotify's rule instead: 4px below 1024px and 8px from it (a tablet is a medium device in Spotify's terms), one `--artwork-radius` value (`docs/design/RECONCILIATION.md` section 18).
- **`sm` (8px):** Form input fields, dropdown select triggers, and secondary action buttons.
- **`md` (10px):** Primary submit buttons and stat block containers.
- **`lg` (14px):** Interactive cards, modal panels, and the heatmap canvas frame.
- **`full` (999px):** Navigation pills, segment control bars, and toggle switches.

### Named Rules
**The Radius Hierarchy Rule.** Internal elements must never have a larger corner radius than their parent container (e.g., an 8px input sits inside a 14px card, never the reverse).

## Components

### Buttons
- **Primary:** Velvet Royal Violet fill (`#6a4baf` / `#b39dde`), cream text (`#faf8f3` / `#0e0c12`), 10px radius, padding `0.625rem 1.25rem`. Subtle `translateY(-1px)` on hover with crisp color shift.
- **Secondary / Card:** Card surface fill (`--ss-surface-card`), 1px hairline border (`#e5dfd1` / `#2a2434`), strong ink text, 8px radius.
- **Ghost:** Transparent fill, muted ink text, transitions to soft accent on hover.

### Inputs & Form Fields
- **Container:** Card surface fill, 1px hairline border (`#e5dfd1`), 8px radius, padding `0.5rem 0.75rem`.
- **Typography:** `input-mono` font, tabular alignment.
- **Focus:** 2px Velvet Royal Violet focus ring with zero outline offset.
- **Mobile Rule:** Minimum rendered `font-size: 1rem` (16px) on mobile viewports to prevent iOS auto-zoom behavior.

### Segmented Controls & Mode Tabs
- **Track:** Page canvas background (`--color-base-100`: `#faf7f0` / `#0e0c12`), 1px hairline border, 8px radius (`--radius-sm`), 3px internal padding at scale 1. The contrast figures below are measured on this fill.
- **Option text and selected option (lifted, `docs/design/RECONCILIATION.md` section 20):** the goal is WCAG AA throughout (4.5:1 for text, 3:1 for non-text); the 7:1 figures below are the aim for unselected text, not a gate for every cell. Unselected option text takes the body ink token (8.71:1 light, 10.61:1 dark on the track). The selected option is a soft accent tint with primary text (5.47:1 light, 6.38:1 dark on the tint, held at the 4.5:1 AA floor by owner exception) and a 1px outline from `--shell-selected-outline` (`#775ab5` 5.01:1 light, `#8a79ab` 5.00:1 dark against the track, and at least 4.5:1 on every surface a selected option sits on; `Highlight` under forced colours). An unselected option deepens to the base-content ink on hover (no new token). The selected option carries no `--ss-shadow-chip` elevation. One rule in `static/css/shell.css` serves "Rank by", both unmatched-albums controls and the Results "Sort leaderboard" buttons.
- **Index mode switch:** shares the selected look above. Its unselected label is the muted token (`#6c6676` 5.17:1 light, `#908a9a` 5.82:1 dark on the track) and its hover is the primary colour; the gate holds that one cell at 4.5:1 by a second owner exception.
- **Disabled Segment:** Kept visible and dimmed to 40% opacity, never removed; the help under the Show row states the reason.
- **Unmatched albums control:** the index card's "Unmatched albums" field (Hide / Include, `name="include_unmatched"`, values 0 / 1; it shares a row with "Show" in equal halves from 860px and stacks below it, and its help line is visible only while Include is chosen) and the Results side rail's "Unmatched albums" control (Hide / Include, `name="results_albums"`) are two-option segmented controls of native radios. The option rules live in `static/css/shell.css` so both pages share them. Help text under them takes the body ink token (7:1 or better), not the muted one. The kit's Switch has no shipped instance: the app's two-state idioms are the header's Light / Dark pill and this segmented control (`docs/design/RECONCILIATION.md` section 20).

### Results Row: Unmatched Variant
- **When:** an include run (the index card's "Unmatched albums" control set to Include) lists albums Spotify and Deezer could not match. They are ranked by play count only.
- **Row:** plain rank and title, no link; the cover slot is the two-tone wash with initials; under the artist a small mono marker in the provider-badge slot says "Not Found" or "Unavailable" in the body ink token; the release cell reads "unknown" in the same token until MusicBrainz finds the original release, then shows it as YYYY-MM (filled in place while the check runs, rendered by the server after it ends).
- **Unmatched albums control:** "Unmatched albums" (Hide / Include, Include selected on an include run) sits under the Sort leaderboard control. Hide hides those rows, ranks and totals recompute, and Listening Time is enabled; Include returns them and Listening Time is dimmed again with its reason.

### Results Row: Listening-Time Ranking
- **Rule:** while the Results page ranks by listening time, an album with no listening time (none or zero) is dropped from the ranking and its row is hidden. The remaining rows are renumbered 1..n in the rank column. Ranking by track plays brings the dropped albums back with their play-count ranks.
- **Header figures:** Total Albums, Top artist and Scrobbles keep describing the whole result under either ranking; the Unmatched albums Hide control recomputes them as it always has.
- **Note and toast:** a short note under the stats grid states how many albums with no listening time are hidden, and the toast on switching to listening time names the same count. Neither shows when no album is dropped or when ranking by track plays.
- **One rule, two places:** the server applies it when a run starts in listening-time mode and the browser applies it when the page is switched, so both show the same leaderboard. Rows hidden by the Unmatched albums control stay hidden whatever the ranking.

### Heatmap Grid
- **Frame:** 14px radius, `--heatmap-surface` fill and 1px border.
- **Cells:** 2px corner radius, 2px grid gap on desktop (1px on mobile), mapped across the 7-stop `rocket_r` ramp.

### Heatmap Streamgraph
- **Placement:** Desktop layout only (860px and up). It sits under the grid inside the frame and its week positions line up with the grid's columns. The result uses the original page gaps and normal document flow, which may extend past a short viewport. The chart reserves 25rem from initial render so its tooltip fits without internal vertical scrolling in the grid or panel. Narrow screens and results stored without weekly artist data show the grid alone.
- **Geometry:** Featured artists alone determine the baseline and stack. The common linear scale fits the complete halo envelope. Each halo margin adds one eighth of the remaining plays in count units; residual-only weeks remain visible. An all-zero payload draws no stream. Month labels reuse the heatmap's calendar positions along the bottom axis.
- **Scrubber panel:** Opens beside the hovered column and lists artists with plays that week, followed by a divider and the actual "Everything else" count. Circular markers identify the artists and the neutral residual. Selecting an artist marks its row and dims other ribbons; selecting the residual leaves them undimmed. The chart is one Tab stop, moved with arrow keys, Home and End.
- **Motion:** The layer dimming fades over 150ms, which `prefers-reduced-motion: reduce` sets to zero.

## Do's and Don'ts

### Do:
- **Do** use `degular` strictly for display words and `gotham` strictly for display numbers (the Results stat row's Top Artist name is the one exception).
- **Do** author all font sizes, line heights, and layout spacing in `rem` units.
- **Do** preserve 4.5:1 text contrast for all muted copy (`#6c6676` light, `#908a9a` dark).
- **Do** keep cards and panels flat at rest with 1px hairline borders.
- **Do** treat Top Albums and Heatmap as equal-standing peer modes on the index screen.

### Don't:
- **Don't** use `font-weight: 500` or `font-weight: 600` anywhere in the interface.
- **Don't** introduce generic cool SaaS greys (`#e5e7eb`, `#1f2937`).
- **Don't** add decorative box shadows to resting cards or panels.
- **Don't** use primary violet as a full-bleed background for content sections.
- **Don't** use React or client-side SPA frameworks; ScrobbleScope is server-rendered Flask + Jinja templates.
