import * as React from "react";

/**
 * Centred dialog. Two shipped uses: the welcome/info sheet on the index page and the
 * quick view of unmatched albums on results.
 */
export interface ModalProps {
  open?: boolean;
  /** Serif, 20px — the modal title is display type, not UI type. */
  title?: React.ReactNode;
  children?: React.ReactNode;
  /** Action row, right-aligned. Usually one Button. */
  footer?: React.ReactNode;
  onClose?: () => void;
  width?: number;
}
