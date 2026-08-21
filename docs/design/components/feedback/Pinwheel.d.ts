import * as React from "react";

/**
 * The breathing pinwheel — ScrobbleScope's only loading indicator, built from the "S"
 * of the wordmark. Fixed asset: 2.5s cycle, 1080° rotation, 5.4-unit blade expansion.
 * Never restyle the motion, never swap it for a spinner.
 */
export interface PinwheelProps {
  /** Rendered px. 132 on desktop, ~96–112 on mobile. */
  size?: number;
  label?: string;
  /** Set false only for static exports (print, thumbnails). */
  animate?: boolean;
}
