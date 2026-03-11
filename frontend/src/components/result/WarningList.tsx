import type { NodeConversionResult } from "../../types/ir";

export default function WarningList({ results }: { results: NodeConversionResult[] }) {
  const warnings = results.filter((r) => r.warnings.length > 0 || r.status === "unmappable");
  if (warnings.length === 0) return null;

  return (
    <div className="alert alert--warning" style={{ marginTop: 24 }}>
      <div style={{ fontWeight: 700, marginBottom: 12, fontSize: "0.85rem" }}>
        ⚠ Warnings & Issues ({warnings.length})
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {warnings.map((r) => (
          <div
            key={r.source_node_id}
            style={{
              padding: "10px 14px",
              background: "rgba(0,0,0,0.15)",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.82rem",
              lineHeight: 1.5,
            }}
          >
            <span style={{ fontWeight: 700, fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
              {r.source_node_type}
            </span>
            <span style={{ opacity: 0.6, marginLeft: 6, fontFamily: "var(--font-mono)", fontSize: "0.7rem" }}>
              {r.source_node_id}
            </span>
            {r.status === "unmappable" && (
              <span style={{ color: "var(--c-red)", marginLeft: 8 }}>
                — No Dify equivalent
              </span>
            )}
            {r.warnings.map((w, i) => (
              <span key={i} style={{ marginLeft: 8 }}>— {w}</span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
