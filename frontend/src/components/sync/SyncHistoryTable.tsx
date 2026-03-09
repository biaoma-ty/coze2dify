interface SyncHistoryItem {
  id: string;
  trigger_type: string;
  workflows_synced: number;
  workflows_failed: number;
  conflicts_count: number;
  started_at: string;
  status: string;
}

export default function SyncHistoryTable({ items }: { items: SyncHistoryItem[] }) {
  if (items.length === 0) {
    return (
      <div className="empty-state card" style={{ borderStyle: "dashed" }}>
        <div className="empty-state__icon">📋</div>
        <p className="empty-state__text">No sync history yet</p>
        <p style={{ fontSize: "0.78rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
          Run your first sync to see results here
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
            <th>Trigger</th>
            <th>Synced</th>
            <th>Failed</th>
            <th>Conflicts</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>{item.started_at}</td>
              <td>
                <span className="badge badge--mapped">{item.trigger_type}</span>
              </td>
              <td style={{ fontFamily: "var(--font-mono)" }}>{item.workflows_synced}</td>
              <td style={{ fontFamily: "var(--font-mono)", color: item.workflows_failed > 0 ? "var(--c-red)" : undefined }}>
                {item.workflows_failed}
              </td>
              <td style={{ fontFamily: "var(--font-mono)", color: item.conflicts_count > 0 ? "var(--c-amber)" : undefined }}>
                {item.conflicts_count}
              </td>
              <td>
                <span className={`badge badge--${item.status === "completed" ? "mapped" : item.status === "failed" ? "unmappable" : "partial"}`}>
                  {item.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
