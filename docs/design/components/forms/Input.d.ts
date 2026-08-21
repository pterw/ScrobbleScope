import * as React from "react";

/** Single-line text or number input. Numbers use `mono` so digits stay tabular. */
export interface InputProps {
  id?: string;
  name?: string;
  type?: "text" | "number" | "search";
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** JetBrains Mono — use for years, counts, anything numeric. */
  mono?: boolean;
  /** Shows the green check used by the live Last.fm username check. */
  valid?: boolean;
  invalid?: boolean;
  disabled?: boolean;
  inputMode?: "text" | "numeric";
}
