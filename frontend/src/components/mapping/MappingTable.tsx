import type { NodeConversionResult } from "../../types/ir";
import StatusBadge from "./StatusBadge";

interface Props {
  results: NodeConversionResult[];
}

export default function MappingTable({ results }: Props) {
  return (
    <div className="table-wrap">
      <table className="c2d-table">
        <thead>
          <tr>
            <th>Source Node</th>
            <th>Target Node</th>
            <th>Status</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.source_node_id}>
              <td>
                <span style={{ fontWeight: 600, color: "var(--c-text-primary)" }}>
                  {r.source_node_type}
                </span>
                <span
                  style={{
                    marginLeft: 8,
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.72rem",
                    color: "var(--c-text-tertiary)",
                  }}
                >
                  {r.source_node_id}
                </span>
              </td>
              <td>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                  {r.target_node_type || "—"}
                </span>
              </td>
              <td>
                <StatusBadge status={r.status} />
              </td>
              <td style={{ color: "var(--c-text-tertiary)", fontSize: "0.8rem" }}>
                {r.warnings.join("; ") || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
