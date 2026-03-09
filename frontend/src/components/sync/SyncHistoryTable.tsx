import type { SyncHistoryEntry } from "../../types/sync";

interface Props {
  items: SyncHistoryEntry[];
  selectedId?: string;
  onSelect?: (item: SyncHistoryEntry) => void | Promise<void>;
}

function statusBadgeClass(status: SyncHistoryEntry["status"]) {
  switch (status) {
    case "completed":
      return "badge--mapped";
    case "partial":
      return "badge--partial";
    case "failed":
      return "badge--unmappable";
    default:
      return "badge--skipped";
  }
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
}

export default function SyncHistoryTable({ items, selectedId, onSelect }: Props) {
  if (items.length === 0) {
    return (
      <div className="empty-state card" style={{ borderStyle: "dashed" }}>
        <div className="empty-state__icon">📋</div>
        <p className="empty-state__text">No sync history yet</p>
        <p style={{ fontSize: "0.78rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
          Run your first sync to persist a manual sync result
        </p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="c2d-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Config</th>
            <th>Created</th>
            <th>Updated</th>
            <th>Skipped</th>
            <th>Blocked</th>
            <th>Failed</th>
            <th>Status</th>
            {onSelect && <th />}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const blocked = item.summary.unsupported + item.summary.conflicts;
            const isSelected = item.id === selectedId;

            return (
              <tr
                key={item.id}
                style={isSelected ? { background: "var(--c-surface-2)" } : undefined}
              >
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                  {formatTimestamp(item.started_at)}
                </td>
                <td>{item.sync_config_name || "Manual Sync"}</td>
                <td style={{ fontFamily: "var(--font-mono)", color: item.summary.created > 0 ? "var(--c-green)" : undefined }}>
                  {item.summary.created}
                </td>
                <td style={{ fontFamily: "var(--font-mono)", color: item.summary.updated > 0 ? "var(--c-blue)" : undefined }}>
                  {item.summary.updated}
                </td>
                <td style={{ fontFamily: "var(--font-mono)" }}>{item.summary.skipped}</td>
                <td style={{ fontFamily: "var(--font-mono)", color: blocked > 0 ? "var(--c-amber)" : undefined }}>
                  {blocked}
                </td>
                <td style={{ fontFamily: "var(--font-mono)", color: item.summary.failed > 0 ? "var(--c-red)" : undefined }}>
                  {item.summary.failed}
                </td>
                <td>
                  <span className={`badge ${statusBadgeClass(item.status)}`}>{item.status}</span>
                </td>
                {onSelect && (
                  <td style={{ width: 120 }}>
                    <button
                      className={isSelected ? "btn btn-secondary" : "btn btn-ghost"}
                      style={{ padding: "6px 12px", fontSize: "0.74rem" }}
                      onClick={() => void onSelect(item)}
                    >
                      {isSelected ? "Viewing" : "View"}
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
