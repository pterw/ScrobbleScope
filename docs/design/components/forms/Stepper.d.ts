import * as React from "react";

/** Numeric stepper for the album thresholds (min plays, min unique tracks). */
export interface StepperProps {
  value?: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
  /** Short mono suffix rendered next to the value, e.g. "×". */
  suffix?: string;
}
