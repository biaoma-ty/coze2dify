import type {
  SyncConflictStrategy,
  SyncRunItem,
} from "../../types/sync";

const STATUS_CONFIG: Array<{
  status: SyncRunItem["status"];
  label: string;
  tone: "green" | "blue" | "amber" | "red" | "slate";
  description: string;
}> = [
  {
    status: "created",
    label: "Created",
    tone: "green",
    description: "New Dify apps that will be created or were created from Coze source workflows.",
  },
  {
    status: "updated",
    label: "Updated",
    tone: "blue",
    description: "Existing Dify apps that will be refreshed with newer converted DSL.",
  },
  {
    status: "conflict",
    label: "Conflicts",
    tone: "amber",
    description: "Source and target both changed and now require an explicit resolution strategy.",
  },
  {
    status: "unsupported",
    label: "Unsupported",
    tone: "amber",
    description: "Changes that were detected but intentionally blocked until policy or feature support exists.",
  },
  {
    status: "failed",
    label: "Failed",
    tone: "red",
    description: "Operations that hit conversion, validation, or target write failures.",
  },
  {
    status: "skipped",
    label: "Skipped",
    tone: "slate",
    description: "Workflows intentionally left unchanged because no target action was needed.",
  },
];

export default function SyncVisualBoard({
  items,
  emptyMessage,
  emptyIcon,
  onResolveConflict,
  resolvingConflictId,
}: {
  items: SyncRunItem[];
  emptyMessage: string;
  emptyIcon: string;
  onResolveConflict?: (conflictId: string, strategy: SyncConflictStrategy) => Promise<void> | void;
  resolvingConflictId?: string | null;
}) {
  if (items.length === 0) {
    return (
      <div className="empty-state card" style={{ borderStyle: "dashed" }}>
        <div className="empty-state__icon">{emptyIcon}</div>
        <p className="empty-state__text">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="change-lane-grid">
      {STATUS_CONFIG.map((lane, index) => {
        const laneItems = items.filter((item) => item.status === lane.status);
        return (
          <section key={lane.status} className={`card change-lane change-lane--${lane.tone} fade-in fade-in-${(index % 4) + 1}`}>
            <div className="change-lane__header">
              <div>
                <div className="change-lane__title">{lane.label}</div>
                <p className="change-lane__description">{lane.description}</p>
              </div>
              <div className="change-lane__count">{laneItems.length}</div>
            </div>

            <div className="change-lane__body">
              {laneItems.length > 0 ? (
                laneItems.map((item, itemIndex) => (
                  <SyncRunCard
                    key={`${item.source_workflow_id || "unknown"}-${item.target_app_id || "target"}-${itemIndex}`}
                    item={item}
                    onResolveConflict={onResolveConflict}
                    resolvingConflictId={resolvingConflictId}
                  />
                ))
              ) : (
                <div className="change-lane__empty">No {lane.label.toLowerCase()} workflows in this set.</div>
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function SyncRunCard({
  item,
  onResolveConflict,
  resolvingConflictId,
}: {
  item: SyncRunItem;
  onResolveConflict?: (conflictId: string, strategy: SyncConflictStrategy) => Promise<void> | void;
  resolvingConflictId?: string | null;
}) {
  const canResolve = Boolean(onResolveConflict && item.status === "conflict" && item.source_workflow_id);
  const resolving = resolvingConflictId === item.source_workflow_id;

  return (
    <article className={`change-item change-item--${toneForRunStatus(item.status)}`}>
      <div className="change-item__header">
        <div>
          <div className="change-item__title">{item.source_workflow_name || item.source_workflow_id || "Unknown workflow"}</div>
          <div className="change-item__meta">
            {item.source_workflow_id || "missing-id"} • {item.action.toUpperCase()}
          </div>
        </div>
        <span className={`badge ${badgeClassForRunStatus(item.status)}`}>{item.status}</span>
      </div>

      <div className="change-item__hint">
        Target {item.target_app_id ? item.target_app_id : "will be determined during write"}
      </div>

      <div className="change-item__note">{item.message}</div>

      {item.delete_policy ? (
        <div className="change-item__note change-item__note--warning">
          {item.delete_policy.label} • {item.delete_policy.summary}
          <div style={{ marginTop: 4 }}>
            Rollback: {item.delete_policy.rollback_requirement}
          </div>
        </div>
      ) : null}

      {item.resolution ? (
        <div className="change-item__note change-item__note--info">
          {item.resolution.status} • {item.resolution.strategy}
          {item.resolution.resolved_at ? ` • ${formatTimestamp(item.resolution.resolved_at)}` : ""}
        </div>
      ) : item.status === "conflict" ? (
        <div className="change-item__note change-item__note--warning">Pending resolution</div>
      ) : null}

      {canResolve ? (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
          <button
            className="btn btn-secondary"
            style={{ padding: "6px 10px", fontSize: "0.72rem" }}
            disabled={resolving}
            onClick={() => void onResolveConflict?.(item.source_workflow_id, "source_wins")}
          >
            {resolving ? "Resolving..." : "Source Wins"}
          </button>
          <button
            className="btn btn-ghost"
            style={{ padding: "6px 10px", fontSize: "0.72rem" }}
            disabled={resolving}
            onClick={() => void onResolveConflict?.(item.source_workflow_id, "target_wins")}
          >
            Keep Target
          </button>
          <button
            className="btn btn-ghost"
            style={{ padding: "6px 10px", fontSize: "0.72rem" }}
            disabled={resolving}
            onClick={() => void onResolveConflict?.(item.source_workflow_id, "manual")}
          >
            Mark Manual
          </button>
        </div>
      ) : null}
    </article>
  );
}

function badgeClassForRunStatus(status: SyncRunItem["status"]) {
  switch (status) {
    case "created":
    case "updated":
      return "badge--mapped";
    case "skipped":
      return "badge--skipped";
    case "unsupported":
    case "conflict":
      return "badge--partial";
    case "failed":
    default:
      return "badge--unmappable";
  }
}

function toneForRunStatus(status: SyncRunItem["status"]) {
  switch (status) {
    case "created":
      return "green";
    case "updated":
      return "blue";
    case "skipped":
      return "slate";
    case "unsupported":
    case "conflict":
      return "amber";
    case "failed":
    default:
      return "red";
  }
}

function formatTimestamp(value: string | undefined) {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
}
