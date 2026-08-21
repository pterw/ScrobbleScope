import * as React from "react";

export interface ModeTabOption {
  value: string;
  label: string;
  /** Override the square's colour. The Heatmap tab uses the rocket ramp's orange end (`var(--rocket-5)`). */
  color?: string;
}

/**
 * Top-level mode switch: Top albums ⇄ Heatmap. One per page, directly above the form card.
 * This is navigation, not a form control — it swaps the whole working area.
 */
export interface ModeTabsProps {
  options?: ModeTabOption[];
  value?: string;
  onChange?: (value: string) => void;
}
