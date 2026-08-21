import * as React from "react";

/** Binary toggle. Geometry copied from the shipped `#darkSwitch` (2.45rem × 1.25rem, 0.95rem knob). */
export interface SwitchProps {
  checked?: boolean;
  onChange?: (checked: boolean) => void;
  label?: string;
  id?: string;
}
