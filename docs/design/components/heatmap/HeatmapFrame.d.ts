import * as React from "react";

export interface HeatmapStat {
  label: string;
  value: React.ReactNode;
  sub?: string;
}

/**
 * The shipped heatmap surface: warm panel, KPI row, rocket_r legend, grid below.
 * This frame is the reference look the rest of the app is being brought in line with.
 */
export interface HeatmapFrameProps {
  /** 3–4 KPIs max: total scrobbles, daily average, best day, current streak. */
  stats?: HeatmapStat[];
  legend?: boolean;
  children?: React.ReactNode;
}

/** 53×7 day grid. Cells are 11px with a 2px gap and 2px radius; zero days use --heatmap-empty. */
export interface HeatmapGridProps {
  /** Scrobbles per day, oldest first, 7 per column. */
  values?: number[];
  weeks?: number;
  /** Upper bound of the colour ramp. Defaults to the max of `values`. */
  max?: number;
  /** Month index (0–11) the window starts at, for the top axis labels. */
  startMonth?: number;
  cell?: number;
  gap?: number;
}

/**
 * Phone layout for the same data: four stacked 13-week strips labelled by season,
 * at a 1px gap so the grid reads as one surface rather than a field of dots.
 * The desktop 53×7 grid is what CSV/JPEG export always renders, regardless of viewport.
 */
export interface HeatmapStripsProps {
  values?: number[];
  max?: number;
  startMonth?: number;
  cell?: number;
  gap?: number;
}

/** Less → More ramp swatch. Reads --rocket-ramp so it can never drift from the grid. */
export interface HeatmapLegendProps {
  width?: number;
}

/** Sample the rocket_r scale at t ∈ [0,1]. */
export declare function rocket(t: number): string;
