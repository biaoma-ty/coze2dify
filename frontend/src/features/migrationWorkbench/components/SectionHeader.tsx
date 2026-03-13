import type { ReactNode } from "react";

interface SectionHeaderProps {
  children: ReactNode;
  action?: ReactNode;
}

export default function SectionHeader({ children, action }: SectionHeaderProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 14,
      }}
    >
      <h2 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>{children}</h2>
      {action}
    </div>
  );
}

