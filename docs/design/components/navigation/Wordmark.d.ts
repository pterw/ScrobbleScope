import * as React from "react";

/**
 * The real ScrobbleScope wordmark: five purple waveform bars + geometric letterforms + small-caps
 * tagline. Fixed asset — scale is the only permitted change. Never redraw or recolour it.
 */
export interface WordmarkProps {
  /** Path to the SVG, relative to the page. Defaults to the assets/ copies in this system. */
  src?: string;
  theme?: "light" | "dark";
  /** Rendered height in px. 92 for the index hero, 38 in the app header bar. */
  height?: number;
  /** false selects the lockup files — the wordmark without the small-caps tagline. */
  tagline?: boolean;
  /** Set false to freeze the visualiser bars (print, thumbnails, static exports). */
  animate?: boolean;
  alt?: string;
}

/** Compact text lockup (serif italic + purple dot) for tight headers where the full mark won't fit. */
export interface WordmarkLockupProps {
  size?: number;
}
