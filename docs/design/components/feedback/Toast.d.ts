import * as React from "react";

/**
 * Confirmation for an action that produces a file or has no visible result —
 * "CSV exported", "Image saved". Bottom-right, auto-dismissing.
 */
export interface ToastProps {
  /** Mono uppercase kicker, e.g. "EXPORTED". */
  title?: string;
  message?: React.ReactNode;
  tone?: "info" | "success" | "warning" | "error";
  onClose?: () => void;
}

/** Fixed bottom-right container. Stack newest at the bottom, max 3 visible. */
export interface ToastStackProps {
  children?: React.ReactNode;
}
