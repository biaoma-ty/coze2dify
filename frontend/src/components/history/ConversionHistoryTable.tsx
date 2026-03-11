import { Link } from "react-router-dom";
import type { ConversionHistoryItem } from "../../types/ir";
import { usePlatformStore } from "../../store/platformStore";

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function shortenId(value: string): string {
  return value.length > 14 ? `${value.slice(0, 14)}…` : value;
}

function getStatusTone(status: string): "mapped" | "partial" | "unmappable" | "skipped" {
  if (status === "converted" || status === "written" || status === "updated") {
    return "mapped";
  }
  if (status === "failed" || status === "error" || status === "write_failed") {
    return "unmappable";
  }
  if (status === "skipped") {
    return "skipped";
  }
  return "partial";
}

function getSourceLabel(sourceType: string): string {
  if (sourceType === "api") return "Coze API";
  if (sourceType === "database") return "Coze DB";
  if (sourceType === "upload") return "Upload";
  return sourceType;
}

export default function ConversionHistoryTable({ items }: { items: ConversionHistoryItem[] }) {
  const difyApiBase = usePlatformStore((s) => s.difyApiBase);

  return (
    <div className="table-wrap">
      <table className="c2d-table" style={{ minWidth: 1080 }}>
        <thead>
          <tr>
            <th>Workflow</th>
            <th>Source</th>
            <th>Created</th>
            <th>Status</th>
            <th>Report</th>
            <th>Dify</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const report = item.report_summary;
            const writeResult = item.write_result;
            const completedLabel = item.completed_at ? `Done ${formatTimestamp(item.completed_at)}` : "Still in progress";
            const difyAppUrl =
              writeResult?.app_id && difyApiBase
                ? `${difyApiBase.replace(/\/$/, "")}/app/${writeResult.app_id}/workflow`
                : null;

            return (
              <tr key={item.conversion_id}>
                <td>
                  <div style={{ display: "grid", gap: 4 }}>
                    <span style={{ color: "var(--c-text-primary)", fontWeight: 600 }}>
                      {item.source_workflow_name || report?.workflow_name || item.source_workflow_id}
                    </span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.76rem", color: "var(--c-text-tertiary)" }}>
                      #{item.conversion_id} · {item.source_workflow_id}
                    </span>
                  </div>
                </td>
                <td>
                  <div style={{ display: "grid", gap: 6 }}>
                    <span className="badge badge--skipped">{getSourceLabel(item.source_type)}</span>
                    <span style={{ fontSize: "0.76rem", color: "var(--c-text-tertiary)" }}>
                      {item.source_type === "upload" ? "Imported file" : "Persisted conversion"}
                    </span>
                  </div>
                </td>
                <td>
                  <div style={{ display: "grid", gap: 4 }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.76rem", color: "var(--c-text-primary)" }}>
                      {formatTimestamp(item.created_at)}
                    </span>
                    <span style={{ fontSize: "0.74rem", color: "var(--c-text-tertiary)" }}>
                      {completedLabel}
                    </span>
                  </div>
                </td>
                <td>
                  <div style={{ display: "grid", gap: 6 }}>
                    <span className={`badge badge--${getStatusTone(item.status)}`}>{item.status}</span>
                    <span style={{ fontSize: "0.76rem", color: "var(--c-text-tertiary)" }}>
                      {item.error_message
                        ? item.error_message
                        : writeResult?.app_id
                          ? `${writeResult.mode === "update" ? "Updated" : "Created"} app`
                          : "Ready for review"}
                    </span>
                  </div>
                </td>
                <td>
                  {report ? (
                    <div style={{ display: "grid", gap: 4, minWidth: 180 }}>
                      <span style={{ color: "var(--c-text-primary)", fontSize: "0.8rem" }}>
                        {report.total_nodes} nodes · {report.mapped_count} mapped
                      </span>
                      <span style={{ fontSize: "0.74rem", color: "var(--c-text-tertiary)" }}>
                        {report.partial_count} partial · {report.unmappable_count} unmappable · {report.skipped_count} skipped
                      </span>
                      <span
                        style={{
                          fontSize: "0.74rem",
                          color:
                            report.errors_count > 0
                              ? "var(--c-red)"
                              : report.warnings_count > 0
                                ? "var(--c-amber)"
                                : "var(--c-text-tertiary)",
                        }}
                      >
                        {report.errors_count} errors · {report.warnings_count} warnings
                      </span>
                    </div>
                  ) : (
                    <span style={{ color: "var(--c-text-tertiary)" }}>No report summary</span>
                  )}
                </td>
                <td>
                  {writeResult?.app_id ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <span style={{ color: "var(--c-text-primary)", fontSize: "0.8rem" }}>
                        {writeResult.mode === "update" ? "Updated" : "Created"} {shortenId(writeResult.app_id)}
                      </span>
                      <span style={{ fontSize: "0.74rem", color: "var(--c-text-tertiary)" }}>
                        {formatTimestamp(writeResult.written_at || item.completed_at)}
                      </span>
                      {writeResult.target?.display_url ? (
                        <span style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
                          {writeResult.target.display_url}
                        </span>
                      ) : null}
                      {difyAppUrl ? (
                        <a
                          href={difyAppUrl}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: "0.76rem", color: "var(--c-accent)" }}
                        >
                          Open in Dify
                        </a>
                      ) : null}
                    </div>
                  ) : item.error_message ? (
                    <div style={{ display: "grid", gap: 4 }}>
                      <span style={{ color: "var(--c-red)", fontSize: "0.78rem" }}>{item.error_message}</span>
                      {item.audit?.last_write?.target?.display_url ? (
                        <span style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
                          {item.audit.last_write.target.display_url}
                        </span>
                      ) : null}
                    </div>
                  ) : (
                    <span style={{ color: "var(--c-text-tertiary)" }}>Not written yet</span>
                  )}
                </td>
                <td>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <Link
                      to={`/diff/${item.conversion_id}`}
                      className="btn btn-ghost"
                      style={{ padding: "8px 12px", fontSize: "0.78rem" }}
                    >
                      View diff
                    </Link>
                    <Link
                      to={`/result/${item.conversion_id}`}
                      className="btn btn-secondary"
                      style={{ padding: "8px 12px", fontSize: "0.78rem" }}
                    >
                      View result
                    </Link>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
