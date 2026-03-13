import type { ButtonHTMLAttributes, ReactNode } from "react";
import { C } from "../theme";

type WorkbenchButtonVariant = "primary" | "secondary" | "success" | "danger";

interface WorkbenchButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: WorkbenchButtonVariant;
  compact?: boolean;
  children: ReactNode;
}

export default function WorkbenchButton({
  variant = "secondary",
  compact = false,
  children,
  style,
  ...props
}: WorkbenchButtonProps) {
  const scheme = {
    secondary: { bg: C.s2, bd: C.bdL, c: C.tx },
    primary: { bg: C.accD, bd: `${C.acc}40`, c: C.acc },
    success: { bg: C.okD, bd: `${C.ok}40`, c: C.ok },
    danger: { bg: C.errD, bd: `${C.err}40`, c: C.err },
  }[variant];

  return (
    <button
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: compact ? "3px 9px" : "6px 13px",
        fontSize: compact ? 11 : 12,
        fontWeight: 600,
        fontFamily: C.ft,
        background: scheme.bg,
        border: `1px solid ${scheme.bd}`,
        borderRadius: 5,
        color: scheme.c,
        cursor: "pointer",
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
}
