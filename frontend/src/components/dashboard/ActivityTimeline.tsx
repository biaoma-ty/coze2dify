import { Link } from "@umijs/max";
import { useTranslation } from "react-i18next";
import { GitCompare, RefreshCw } from "lucide-react";
import type { ConversionHistoryItem } from "../../types/ir";
import type { SyncHistoryEntry } from "../../types/sync";
import EmptyState from "../common/EmptyState";

type TimelineEntry =
  | { kind: "conversion"; item: ConversionHistoryItem; timestamp: string }
  | { kind: "sync"; item: SyncHistoryEntry; timestamp: string };

function mergeAndSort(
  conversions: ConversionHistoryItem[],
  syncRuns: SyncHistoryEntry[],
): TimelineEntry[] {
  const entries: TimelineEntry[] = [];

  for (const c of conversions) {
    entries.push({
      kind: "conversion",
      item: c,
      timestamp: c.created_at || "",
    });
  }

  for (const s of syncRuns) {
    entries.push({
      kind: "sync",
      item: s,
      timestamp: s.started_at || "",
    });
  }

  entries.sort((a, b) => {
    if (!a.timestamp) return 1;
    if (!b.timestamp) return -1;
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  return entries.slice(0, 10);
}

function formatRelativeTime(value: string | null): string {
  if (!value) return "";
  const diff = Date.now() - new Date(value).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function getStatusBadgeClass(status: string): string {
  if (status === "converted" || status === "written" || status === "updated" || status === "completed") {
    return "badge--mapped";
  }
  if (status === "failed" || status === "error" || status === "write_failed") {
    return "badge--unmappable";
  }
  if (status === "partial") {
    return "badge--partial";
  }
  return "badge--skipped";
}

interface ActivityTimelineProps {
  conversions: ConversionHistoryItem[];
  syncRuns: SyncHistoryEntry[];
}

export default function ActivityTimeline({
  conversions,
  syncRuns,
}: ActivityTimelineProps) {
  const { t } = useTranslation();
  const entries = mergeAndSort(conversions, syncRuns);

  if (entries.length === 0) {
    return (
      <EmptyState
        icon={GitCompare}
        text={t("dashboard.recentActivityEmpty")}
      />
    );
  }

  return (
    <div className="activity-timeline">
      {entries.map((entry, index) => {
        if (entry.kind === "conversion") {
          const c = entry.item;
          return (
            <Link
              key={`c-${c.conversion_id}-${index}`}
              to={`/migrate/diff/${c.conversion_id}`}
              className="activity-timeline__item"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div className="activity-timeline__icon activity-timeline__icon--conversion">
                <GitCompare size={16} />
              </div>
              <div className="activity-timeline__content">
                <div className="activity-timeline__title">
                  {c.source_workflow_name || c.source_workflow_id}
                </div>
                <div className="activity-timeline__meta">
                  <span className={`badge ${getStatusBadgeClass(c.status)}`}>
                    {c.status}
                  </span>
                  <span>{formatRelativeTime(c.created_at)}</span>
                </div>
              </div>
            </Link>
          );
        }

        const s = entry.item;
        return (
          <Link
            key={`s-${s.id}-${index}`}
            to={`/sync/history/${s.id}`}
            className="activity-timeline__item"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div className="activity-timeline__icon activity-timeline__icon--sync">
              <RefreshCw size={16} />
            </div>
            <div className="activity-timeline__content">
              <div className="activity-timeline__title">
                {s.sync_config_name || "Manual Sync"}
              </div>
              <div className="activity-timeline__meta">
                <span className={`badge ${getStatusBadgeClass(s.status)}`}>
                  {s.status}
                </span>
                <span>
                  {s.workflows_synced} synced
                </span>
                <span>{formatRelativeTime(s.started_at)}</span>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
