import * as React from "react";

/**
 * Collapsed row that expands in place. Carries the advanced thresholds on the index form:
 * the collapsed state must still show the current values so nothing is hidden, only folded.
 */
export interface DisclosureProps {
  label?: React.ReactNode;
  /** Mono summary of the current state, e.g. "≥10 plays · ≥3 tracks". Always show it. */
  summary?: React.ReactNode;
  open?: boolean;
  onToggle?: (open: boolean) => void;
  children?: React.ReactNode;
}
