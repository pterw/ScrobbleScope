import * as React from "react";

/** Thin determinate hairline under the pinwheel. Never striped, never animated-indeterminate. */
export interface ProgressBarProps {
  /** 0–100. Only show it when the value is real; otherwise show the pinwheel alone. */
  value?: number;
  width?: number | string;
  /** Mono uppercase phase label, e.g. "Fetching page 3 of 45". */
  label?: string;
}
