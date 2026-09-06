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
  surface-page: "#faf8f3"
  surface-page-dark: "#0e0c12"
  surface-sunken: "#f0ebe0"
  surface-sunken-dark: "#1a1622"
  surface-card: "#fcfbf8"
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
  heatmap-empty: "#e8e2d6"
  heatmap-empty-dark: "#262230"
  good: "#2f7a4a"
  good-dark: "#6fcf97"
  bad: "#b03434"
  bad-dark: "#e07070"
typography:
  display:
    fontFamily: "instrument-serif, Georgia, serif"
    fontSize: "2rem"
    fontWeight: 400
    lineHeight: 1.05
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "instrument-serif, Georgia, serif"
    fontSize: "1.5rem"
    fontWeight: 400
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
- **Warm Archival Ground:** Cream paper (`#faf8f3`) in light mode; deep purple-tinged obsidian (`#0e0c12`) in dark mode.
- **Strict Typographic Role Separation:** Literary serif for editorial words, geometric sans for structural chrome, tabular mono for parameters, and sculpted figures for numeric magnitude.
- **Hairline Architecture:** Structural containment achieved through 1px borders and tonal ground shifts rather than drop shadows.
- **Restrained Velvet Accent:** Royal velvet purple (`#6a4baf` / `#b39dde`) applied with extreme parsimony to direct attention.
- **Dense, Traceable Data:** Every metric, ranking, exclusion, and heatmap cell is readable, verifiable, and grounded in listener evidence.

## Colors

The palette draws from classic printing inks and warm archival paper, accented by a single velvet violet brand tint and the seven-stop scientific `rocket_r` density ramp.

### Primary
- **Velvet Royal Violet** (`#6a4baf` light / `#b39dde` dark): The singular brand accent. Reserved strictly for primary action buttons, focused input outlines, active navigation indicators, and the brand lockup bars.
- **Accent Soft** (`#efe9fa` light / `#2a1f44` dark): Gentle tint used for selected radio chips, active table row highlights, and subtle keyboard-focus halos.

### Neutral
- **Page Canvas** (`#faf8f3` light / `#0e0c12` dark): The root background canvas. Warmed off pure white to evoke rag paper; dark mode uses an obsidian ground with faint violet warmth rather than neutral computer grey.
- **Sunken Well** (`#f0ebe0` light / `#1a1622` dark): Recessed ground used for the index form column and secondary structural wells.
- **Card Surface** (`#ffffff` light / `#181520` dark): Crisp elevated ground for interactive cards, data tables, and input containers.
- **Ink Strong** (`#1a1820` light / `#f1ede4` dark): Maximum-contrast text color for page titles, section headings, values, and primary labels.
- **Ink Body** (`#4a4456` light / `#c5bfb1` dark): Readable secondary text color for descriptive paragraphs and form field descriptions.
- **Ink Muted** (`#6c6676` light / `#908a9a` dark): Muted metadata, field hint copy, and timestamps; tuned to maintain 4.5:1 contrast against light and dark surfaces.
- **Hairline Border** (`#e5dfd1` light / `#2a2434` dark): The universal 1px structural dividing line for cards, inputs, and segment dividers.
- **Well Divider** (`#8a867e` light / `#68646f` dark): Higher-contrast vertical boundary separating the hero stage from the configuration well.

### Heatmap & Status
- **Rocket Stop 5 (Tangerine)** (`#f0903a`): The single warm accent drawn from seaborn's `rocket_r` ramp, used exclusively for the Heatmap mode indicator mark.
- **Heatmap Empty** (`#e8e2d6` light / `#262230` dark): Resting color of days with zero scrobbles, warmed to match the parchment ground.
- **Good / Success** (`#2f7a4a` light / `#6fcf97` dark): Forest pine for successful cache hits and validated inputs.
- **Bad / Error** (`#b03434` light / `#e07070` dark): Terracotta crimson for validation errors, private profile alerts, and failed jobs.

### Named Rules
**The Ink-and-Parchment Rule.** Surfaces must never default to cold `#ffffff` or browser-default dark `#121212`. Light mode is cream paper (`#faf8f3`); dark mode is deep obsidian ink (`#0e0c12`).
**The Accent Restraint Rule.** Primary violet is used on ≤10% of any screen surface. Its rarity is what gives it authority.
**The Status Hairline Rule.** Status colors appear exclusively as 3px indicator rules, icon strokes, or monospace kickers—never as saturated full-bleed background fills.

## Typography

Type is served by Adobe Fonts kit `rwy8ghw`. Five distinct families each perform a single, non-negotiable duty.

**Display Font:** `instrument-serif` (Georgia, serif fallback)
**UI Body & Chrome Font:** `akzidenz-grotesk-next-pro` (ui-sans-serif, system-ui fallback)
**Figure Font:** `gotham` (ui-sans-serif fallback, Book weight only)
**Code & Data Mono:** `input-mono` (ui-monospace, monospace fallback)
**Eyebrow & Label Mono:** `input-mono-narrow` ("input-mono", monospace fallback)

**Character:** The pairing of an expressive literary serif with clinical Swiss grotesque and technical mono evokes a vintage monograph or catalog raisonee.

### Hierarchy
- **Display** (400 weight, `2rem` to `3rem`, line-height `1.05`, tracking `-0.01em`): Editorial hero phrases and main page banners (`instrument-serif`).
- **Headline** (400 weight, `1.5rem`, line-height `1.15`): Section headings and mode titles (`instrument-serif`).
- **Title** (700 weight, `1rem`, line-height `1.25`): Card titles, form section labels, and modal headers (`akzidenz-grotesk-next-pro`).
- **Body** (400 weight, `1rem`, line-height `1.5`): Paragraph descriptions, documentation, and error explanations (`akzidenz-grotesk-next-pro`). Max measure 65–75ch.
- **Label / Eyebrow** (400 weight, `0.75rem` / 12px, line-height `1`, tracking `0.12em`, uppercase): Metadata tags, field labels, table headers, and status flags (`input-mono-narrow`).
- **Figure Numerals** (400 weight, `1.125rem` to `2.5rem`, tabular): Large quantitative readouts, play counts, and hours listened (`gotham`).

### Named Rules
**The Role Segregation Rule.** Gotham gets the numbers, Instrument Serif gets the words. They never compete for the same slot. Gotham is never used for UI chrome and never rendered at bold weight.
**The No-Medium Rule.** The Adobe kit serves weights 300, 400, and 700 only. Never use `font-weight: 500` or `font-weight: 600`. Hierarchy is established through scale, contrast, case, and tracking.
**The Narrow Eyebrow Rule.** Anything letterspaced in uppercase between 9px and 12px must use `input-mono-narrow` to eliminate horizontal crowding and prevent field hint clipping.

## Layout

The spatial model uses a 4px baseline grid expressed strictly in `rem` units (at a 16px root: 4px = `0.25rem`, 8px = `0.5rem`, 12px = `0.75rem`, 16px = `1rem`, 24px = `1.5rem`, 32px = `2rem`, 48px = `3rem`).

### Desktop & Mobile Grid
- **Desktop Index Stage:** Asymmetric two-column composition (`3fr 4fr`). The left hero stage hosts the editorial title and brand lockup with generous padding (`3.5rem`). The right sunken well hosts the configuration form (capped at `27.5rem` base, centering vertically when fitting).
- **Breakpoint Stacking:** Collapses to a single vertical column below `860px` (`53.75rem`).
- **Heatmap Stage:** Centered frame using `84vw` (capped at `120rem`) for wide viewports, scaling down to a minimum `73rem` scrollable canvas on mobile.
- **Mobile Navigation:** At mobile viewports, destination pills organize in a single line across the header width with zero horizontal scrollbars, preserving the 44px minimum touch target height; the theme toggle sits below page content.

### Named Rules
**The Fixed Composition Rule.** The desktop index composition anchors to the top and retains natural height without shifting baseline when form disclosure panels open.
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
- **`xs` (4px):** Album artwork thumbnails, tiny pill tags, and sub-metric chips.
- **`sm` (8px):** Form input fields, dropdown select triggers, and secondary action buttons.
- **`md` (10px):** Primary submit buttons and stat block containers.
- **`lg` (14px):** Interactive cards, modal panels, and the heatmap canvas frame.
- **`full` (999px):** Navigation pills, segment control bars, and toggle switches.

### Named Rules
**The Radius Hierarchy Rule.** Internal elements must never have a larger corner radius than their parent container (e.g., an 8px input sits inside a 14px card, never the reverse).

## Components

### Buttons
- **Primary:** Velvet Royal Violet fill (`#6a4baf` / `#b39dde`), cream text (`#faf8f3` / `#0e0c12`), 10px radius, padding `0.625rem 1.25rem`. Subtle `translateY(-1px)` on hover with crisp color shift.
- **Secondary / Card:** Card surface fill (`#ffffff` / `#181520`), 1px hairline border (`#e5dfd1` / `#2a2434`), strong ink text, 8px radius.
- **Ghost:** Transparent fill, muted ink text, transitions to soft accent on hover.

### Inputs & Form Fields
- **Container:** Card surface fill, 1px hairline border (`#e5dfd1`), 8px radius, padding `0.5rem 0.75rem`.
- **Typography:** `input-mono` font, tabular alignment.
- **Focus:** 2px Velvet Royal Violet focus ring with zero outline offset.
- **Mobile Rule:** Minimum rendered `font-size: 1rem` (16px) on mobile viewports to prevent iOS auto-zoom behavior.

### Segmented Controls & Mode Tabs
- **Track:** Sunken well background (`#f0ebe0` / `#1a1622`), 999px full pill radius, 4px internal padding.
- **Active Segment:** Card surface background, `--ss-shadow-chip` elevation, strong ink text.

### Heatmap Grid
- **Frame:** 14px rounded card surface with 1px border.
- **Cells:** 2px corner radius, 2px grid gap on desktop (1px on mobile), mapped across the 7-stop `rocket_r` ramp.

## Do's and Don'ts

### Do:
- **Do** use `instrument-serif` strictly for display words and `gotham` strictly for display numbers.
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
