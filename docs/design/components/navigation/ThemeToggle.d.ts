import * as React from "react";

/**
 * Light/dark switch. Lives in the page header, not buried in a footer bar —
 * the shipped app hides it at the bottom of every page, which is the wrong place.
 */
export interface ThemeToggleProps {
  theme?: "light" | "dark";
  onChange?: (theme: "light" | "dark") => void;
  compact?: boolean;
}
