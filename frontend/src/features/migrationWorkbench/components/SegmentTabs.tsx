import type { ReactNode } from "react";
import { C } from "../theme";

interface SegmentTabItem<T extends string> {
  key: T;
  label: string;
  icon?: ReactNode;
}

interface SegmentTabsProps<T extends string> {
  items: Array<SegmentTabItem<T>>;
  activeKey: T;
  onChange: (key: T) => void;
}

export default function SegmentTabs<T extends string>({
  items,
  activeKey,
  onChange,
}: SegmentTabsProps<T>) {
  return (
    <div style={{ display: "flex", gap: 1, borderBottom: `1px solid ${C.bd}` }}>
      {items.map((item) => (
        <button
          key={item.key}
          onClick={() => onChange(item.key)}
          style={{
            padding: "8px 14px",
            fontSize: 12,
            fontWeight: activeKey === item.key ? 600 : 400,
            fontFamily: C.ft,
            background: "transparent",
            border: "none",
            borderBottom:
              activeKey === item.key
                ? `2px solid ${C.acc}`
                : "2px solid transparent",
            color: activeKey === item.key ? C.acc : C.tx2,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
          }}
          type="button"
        >
          {item.icon}
          {item.label}
        </button>
      ))}
    </div>
  );
}
