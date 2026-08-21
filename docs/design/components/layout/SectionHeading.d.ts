import * as React from "react";

/** Mono eyebrow + serif headline + optional action row. The standard page/section header. */
export interface SectionHeadingProps {
  /** Mono uppercase kicker, e.g. "TOP ALBUMS · 2025 · PLAY COUNT". */
  eyebrow?: React.ReactNode;
  title?: React.ReactNode;
  /** Italic purple fragment appended to the title — the one flourish the brand allows. */
  accent?: React.ReactNode;
  description?: React.ReactNode;
  size?: "sm" | "md" | "lg";
  actions?: React.ReactNode;
}
