import * as React from "react";

export interface PillOption {
  value: string;
  label: string;
  /** Dimmed to 0.4 and unclickable — how decades outside the user's history are shown. */
  disabled?: boolean;
}

/** Single-select pill row. The decade picker (2020s…1950s) is the canonical use. */
export interface PillGroupProps {
  options?: PillOption[];
  value?: string;
  onChange?: (value: string) => void;
  name?: string;
  centered?: boolean;
}
