import { Handle, Position } from "@xyflow/react";

export default function DifyNode({ data }: { data: { label: string; type: string } }) {
  return (
    <div
      style={{
        padding: "10px 16px",
        background: "var(--c-surface-2)",
        borderRadius: 8,
        border: "1px solid #00d4aa40",
        fontSize: "0.78rem",
        minWidth: 120,
        boxShadow: "0 2px 8px rgba(0, 212, 170, 0.1)",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: "var(--c-accent)" }} />
      <div style={{ fontWeight: 700, color: "var(--c-accent)", marginBottom: 2 }}>{data.label}</div>
      <div style={{ color: "var(--c-text-tertiary)", fontSize: "0.68rem", fontFamily: "var(--font-mono)" }}>
        {data.type}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: "var(--c-accent)" }} />
    </div>
  );
}
