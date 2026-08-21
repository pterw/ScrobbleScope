import * as React from "react";

/**
 * One album in the results leaderboard: rank, cover, title/artist, value, release meta.
 * Replaces the Bootstrap striped table row — rows are separated by a hairline, never by stripes.
 */
export interface AlbumRowProps {
  rank?: number | string;
  title?: string;
  artist?: string;
  /** Mono value — play count ("247") or play time ("18h 42m"). */
  value?: React.ReactNode;
  /** Small mono line under the value — release date or year. */
  meta?: React.ReactNode;
  /** Cover art URL. When absent a deterministic placeholder wash is used. */
  cover?: string;
  coverIndex?: number;
  /** Spotify album URL; makes the title a link. */
  href?: string;
  size?: "md" | "lg";
}
