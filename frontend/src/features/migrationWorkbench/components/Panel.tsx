import type { CSSProperties, ReactNode } from "react";

interface PanelProps {
  children: ReactNode;
  style?: CSSProperties;
}

export default function Panel({ children, style }: PanelProps) {
  return (
    <div
      style={{
        background: "#0c1221",
        border: "1px solid #1c2a48",
        borderRadius: 8,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
