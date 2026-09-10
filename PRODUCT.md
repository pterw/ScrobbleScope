# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is a Last.fm listener with a public profile who wants to
understand their own listening history. Private profiles are unsupported and
must be rejected at entry, before an analysis job starts.

No ScrobbleScope account is required. The product works from listening data
that the Last.fm user has already made public.

## Product Purpose

ScrobbleScope began as a tool for building album-of-the-year lists from a
listener's actual plays. That origin explains the Top Albums defaults: the
current listening year and albums released in that same year. The scope and
filtering granularity have grown since then, but trustworthy personal analysis
remains the purpose.

The product currently provides two forms of analysis:

- **Top Albums** filters and ranks albums for a chosen listening year and
  release period, using either play count or listening time. It explains
  exclusions and supports CSV and image export.
- **Listening Heatmap** shows the latest 365 days as daily listening density,
  with summary statistics that make patterns and streaks legible.

Success means a listener can enter a Last.fm username and get a trustworthy,
useful account of what they played, how long they spent listening, and how
their listening changed over time. Playtime is a first-class answer; the desire
to see it was the original motivation for the product.

## Positioning

ScrobbleScope is an always-accessible, account-free view into a public Last.fm
history rather than a generic chart. It combines Last.fm scrobble evidence with
user-controlled filtering and Spotify metadata, and it shows playtime alongside
play counts. It gives listeners more control and explanation than official
summary charts while staying grounded in their own data.

## Operating Context

The index currently presents Top Albums and Heatmap as peer modes. A listener
supplies a public Last.fm username, selects only the settings relevant to the
active mode, and starts a server-backed analysis. Longer requests report
progress before showing the result.

The interface is server-rendered and responsive. Album analysis can lead to a
ranked result, an explanation of unmatched albums, and downloadable CSV or JPEG
artifacts. Heatmap analysis returns a self-contained view of the latest 365
days.

The repository has two distinct planes. The product plane is the listener's
experience and the analysis it delivers. The development control plane is the
batch, worktree, documentation, review, and verification machinery used to
refine that experience. Control-plane structure must not become product
information architecture.

## Capabilities and Constraints

- Last.fm is the source of listening history and public-profile validation.
- Private Last.fm profiles are not a degraded mode. The entry flow must stop
  them before creating a job and explain that a public profile is required.
- Spotify enriches album results with release dates, artwork, and track
  runtimes; the heatmap does not depend on Spotify.
- Top Albums supports listening-year and release-period filters, configurable
  play and track thresholds, play-count or listening-time ranking, and result
  limits.
- Heatmap covers the latest 365 days and deliberately exposes no date-range
  settings.
- Results must remain traceable to the listener's data. Excluded albums state
  the reason and the change that would include them.
- Top Albums and Heatmap are the current modes, not a permanent ceiling. The
  product structure must leave room for another feature such as Top Songs.
- Batch 21 is an active page-by-page strangler migration from Bootstrap 5 to
  Tailwind CSS and daisyUI. Existing behavior must remain stable, and each page
  uses only its assigned framework stylesheet during the transition. The live
  migration status and next action remain owned by `BATCH21_DEFINITION.md` and
  `PLAYBOOK.md`; this record must not duplicate them.
- The design system is not ready for final extraction. After the migration is
  complete, critique and audit the implemented system, then export the durable
  result. Batch 21 WP-8 owns the final frontend and accessibility audit and
  migration close-out.

## Brand Commitments

- The product name is **ScrobbleScope**.
- Top Albums and Heatmap are the current primary paths, with room for future
  analysis modes.
- The existing wordmark, inline marks, pinwheel, and favicon family are the
  established brand assets.
- The dated `docs/design/` snapshot is historical evidence, not current visual
  authority. Current source, current owner constraints in `AGENT_NOTES.md`, and
  recent decisions in `PLAYBOOK.md` take precedence.
- Product copy addresses the listener as "you," uses sentence case, names
  capabilities in plain language, and avoids invented enthusiasm.

## Evidence on Hand

- The repository contains a working Flask application with both modes, their
  loading and result flows, export behavior, and error handling.
- Current templates, Tailwind source, browser checks, tests, and tracked brand
  assets provide implementation evidence during the migration.
- A live deployment is linked from `README.md`.
- No testimonials, customer logos, usage benchmarks, or other social-proof
  claims are established. Future work must not invent them.

## Product Principles

1. Start with a public Last.fm profile and fail clearly at entry when the
   profile cannot be analyzed.
2. Keep playtime visible as a first-class measure, not a secondary detail.
3. Preserve the AOTY-oriented defaults while allowing deeper filtering and
   other listening views.
4. Prefer exact user data and transparent filtering over generic summaries.
5. Explain why a result was excluded and give the specific corrective action.
6. Reveal only the controls needed for the active mode, without hard-coding a
   two-mode future.
7. Keep product decisions separate from the development control plane.
8. Preserve user-visible behavior while the interface migrates page by page.

## Accessibility & Inclusion

Follow the repository's current UI and accessibility rules in `AGENTS.md`.
Prove behavior in rendered states reachable by keyboard, touch, and scripts.
No formal conformance target has been confirmed.
