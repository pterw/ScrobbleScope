import * as React from "react";

/** Inline, non-dismissing message tied to the content around it: partial data, no matches, fetch errors. */
export interface AlertProps {
  tone?: "info" | "success" | "warning" | "error";
  /** Mono uppercase kicker, e.g. "PARTIAL DATA". */
  title?: string;
  children?: React.ReactNode;
  /** Optional recovery action — a Button, usually secondary. */
  action?: React.ReactNode;
}
