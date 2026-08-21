import * as React from "react";

/** Mono label over a serif number. Used for heatmap KPIs, result summaries and loading stats. */
export interface StatBlockProps {
  /** Uppercase mono key, e.g. "TOTAL SCROBBLES". */
  label?: string;
  value?: React.ReactNode;
  /** Small sans unit trailing the number, e.g. "albums". */
  unit?: string;
  size?: "sm" | "md" | "lg";
  /** Wrap in a bordered card — for the results sidebar. Bare otherwise. */
  bordered?: boolean;
}
