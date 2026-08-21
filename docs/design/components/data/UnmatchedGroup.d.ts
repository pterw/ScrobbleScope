import * as React from "react";

export interface UnmatchedItem {
  album: string;
  artist: string;
  /** Mono right-hand note — how close it came, e.g. "7 plays / 2 tracks". */
  note?: string;
}

/**
 * One reason-category card on the unmatched report: why these albums were excluded,
 * how many, a sample, and the single action that would let them through.
 * Groups are keyed by reason CATEGORY (below threshold, no Spotify match, outside release
 * filter) — not by per-album sentence.
 * @startingPoint section="Results" subtitle="Unmatched reason group with fix hint" viewport="700x300"
 */
export interface UnmatchedGroupProps {
  reason?: string;
  count?: number | string;
  /** One sentence in plain language explaining the category. */
  explanation?: string;
  /** Mono uppercase call to action, e.g. "LOWER TO ≥5 PLAYS TO INCLUDE 23". */
  fix?: string;
  items?: UnmatchedItem[];
}
