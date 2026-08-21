import * as React from "react";

/**
 * Label + inline hint + help text wrapper for any form control. Replaces the "?" tooltip
 * circles in the Bootstrap build: the explanation sits in the label row, always visible.
 */
export interface FieldProps {
  label?: string;
  /** Right-aligned mono micro-hint on the label row, e.g. "2002–2026". */
  hint?: string;
  htmlFor?: string;
  /** Mono help line under the control. Say what the setting does, not what it is. */
  help?: React.ReactNode;
  required?: boolean;
  children?: React.ReactNode;
}
