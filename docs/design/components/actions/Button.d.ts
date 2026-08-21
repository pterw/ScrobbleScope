import * as React from "react";

/**
 * The one button in ScrobbleScope. Solid = the single committing action on a screen
 * (Search, Generate, New search); secondary = everything else; mono = export-bar buttons.
 */
export interface ButtonProps {
  children?: React.ReactNode;
  /** primary = solid ink (light) / solid purple (dark). Only one per screen. */
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  /** Uppercase JetBrains Mono label — used for export / utility bars. */
  mono?: boolean;
  fullWidth?: boolean;
  disabled?: boolean;
  /** Trailing glyph, e.g. the "→" on the submit button. */
  trailing?: React.ReactNode;
  leading?: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  title?: string;
}
