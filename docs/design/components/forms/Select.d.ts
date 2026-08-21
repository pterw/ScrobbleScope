import * as React from "react";

export interface SelectOption {
  value: string;
  label: string;
}

/** Native select with the ScrobbleScope chevron. Used for release scope and result limit. */
export interface SelectProps {
  id?: string;
  name?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options?: SelectOption[];
  disabled?: boolean;
}
