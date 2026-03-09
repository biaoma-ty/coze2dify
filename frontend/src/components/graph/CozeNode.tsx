import { Handle, Position } from "@xyflow/react";

export default function CozeNode({ data }: { data: { label: string; type: string } }) {
  return (
    <div
      style={{
        padding: "10px 16px",
        background: "var(--c-surface-2)",
        borderRadius: 8,
        border: "1px solid #3b82f640",
        fontSize: "0.78rem",
        minWidth: 120,
        boxShadow: "0 2px 8px rgba(59, 130, 246, 0.1)",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: "var(--c-blue)" }} />
      <div style={{ fontWeight: 700, color: "var(--c-blue)", marginBottom: 2 }}>{data.label}</div>
      <div style={{ color: "var(--c-text-tertiary)", fontSize: "0.68rem", fontFamily: "var(--font-mono)" }}>
        {data.type}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: "var(--c-blue)" }} />
    </div>
  );
}
