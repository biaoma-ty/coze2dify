interface Conflict {
  workflow_id: string;
  workflow_name: string;
  source_updated: string;
  target_updated: string;
}

interface Props {
  conflicts: Conflict[];
  onResolve: (workflowId: string, strategy: "source_wins" | "target_wins") => void;
}

export default function ConflictResolver({ conflicts, onResolve }: Props) {
  if (conflicts.length === 0) {
    return (
      <div className="empty-state card" style={{ borderStyle: "dashed" }}>
        <div className="empty-state__icon">✅</div>
        <p className="empty-state__text">No conflicts</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {conflicts.map((c) => (
        <div
          key={c.workflow_id}
          className="card"
          style={{
            padding: 20,
            borderColor: "var(--c-amber)",
            borderLeftWidth: 3,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--c-text-primary)", marginBottom: 6 }}>
                {c.workflow_name}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
                Source: {c.source_updated} · Target: {c.target_updated}
              </div>
            </div>

            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn btn-primary"
                style={{ padding: "6px 14px", fontSize: "0.75rem" }}
                onClick={() => onResolve(c.workflow_id, "source_wins")}
              >
                Use Coze
              </button>
              <button
                className="btn btn-ghost"
                style={{ padding: "6px 14px", fontSize: "0.75rem" }}
                onClick={() => onResolve(c.workflow_id, "target_wins")}
              >
                Keep Dify
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
