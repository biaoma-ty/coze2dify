import type { CSSProperties, ReactNode } from "react";
import { C } from "../theme";
import type { Tone } from "../types";

interface StatusBadgeProps {
  tone: Tone;
  children: ReactNode;
  style?: CSSProperties;
}

const TONE_COLORS: Record<Tone, string> = {
  accent: C.acc,
  info: C.coze,
  success: C.ok,
  warning: C.warn,
  danger: C.err,
  muted: C.tx2,
};

export default function StatusBadge({ tone, children, style }: StatusBadgeProps) {
  const color = TONE_COLORS[tone];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        padding: "2px 7px",
        borderRadius: 4,
        fontSize: 10,
        fontWeight: 700,
        color,
        background: `${color}18`,
        ...style,
      }}
    >
      {children}
    </span>
  );
}
