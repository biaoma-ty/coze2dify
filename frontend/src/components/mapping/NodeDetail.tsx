import type { NodeConversionResult } from "../../types/ir";
import StatusBadge from "./StatusBadge";

export default function NodeDetail({ result }: { result: NodeConversionResult }) {
  return (
    <div className="card card--elevated" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700, color: "var(--c-text-primary)" }}>
          {result.source_node_type}
        </h3>
        <StatusBadge status={result.status} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: "0.82rem" }}>
        <div style={{ display: "flex", gap: 8 }}>
          <span className="label" style={{ minWidth: 80, marginBottom: 0 }}>Source ID</span>
          <span style={{ fontFamily: "var(--font-mono)", color: "var(--c-text-secondary)" }}>
            {result.source_node_id}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <span className="label" style={{ minWidth: 80, marginBottom: 0 }}>Target</span>
          <span style={{ fontFamily: "var(--font-mono)", color: "var(--c-text-secondary)" }}>
            {result.target_node_type || "N/A"}
          </span>
        </div>

        {result.warnings.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <span className="label">Warnings</span>
            <ul style={{ margin: "4px 0 0", paddingLeft: 20 }}>
              {result.warnings.map((w, i) => (
                <li key={i} style={{ color: "var(--c-amber)", fontSize: "0.8rem", marginBottom: 2 }}>
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
