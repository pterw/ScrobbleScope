import * as React from "react";

/**
 * Small mono chip. Three jobs: active filters on results (`soft`), search parameters echoed
 * on the loading screen (`outline`), and release dates on album rows (`solid`).
 */
export interface TagProps {
  children?: React.ReactNode;
  variant?: "soft" | "outline" | "solid";
  title?: string;
}
