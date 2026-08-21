import * as React from "react";

/**
 * The one surface primitive: warm card, hairline border, 14px radius, no drop shadow.
 */
export interface CardProps {
  children?: React.ReactNode;
  /** CSS padding. 16px on mobile, 24px on desktop. */
  padding?: string;
  /** Use --surface-sunken instead of --surface-card, for nested panels. */
  sunken?: boolean;
  style?: React.CSSProperties;
}
