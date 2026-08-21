import * as React from "react";

export interface SegmentOption {
  value: string;
  label: string;
}

/**
 * Two- or three-way exclusive switch inside a form — play count vs play time is the canonical use.
 * For switching whole modes of the app (Top albums / Heatmap) use ModeTabs instead.
 */
export interface SegmentedControlProps {
  options?: SegmentOption[];
  value?: string;
  onChange?: (value: string) => void;
  size?: "sm" | "md";
  fullWidth?: boolean;
}
