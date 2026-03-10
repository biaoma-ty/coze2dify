import { useEffect, useState } from "react";
import SyncVisualBoard from "../components/diff/SyncVisualBoard";
import SyncHistoryTable from "../components/sync/SyncHistoryTable";
import { getSyncHistoryDetail, listSyncHistory } from "../api/sync";
import type { SyncHistoryEntry, SyncRunDetail } from "../types/sync";

export default function SyncHistoryPage() {
  const [history, setHistory] = useState<SyncHistoryEntry[]>([]);
  const [selectedRun, setSelectedRun] = useState<SyncRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const items = await listSyncHistory();
        if (cancelled) {
          return;
        }
        setHistory(items);
        if (items.length > 0) {
          const detail = await getSyncHistoryDetail(items[0].id);
          if (!cancelled) {
            setSelectedRun(detail);
          }
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.response?.data?.detail || e?.message || "Failed to load sync history");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelect = async (entry: SyncHistoryEntry) => {
    setError("");
    try {
      const detail = await getSyncHistoryDetail(entry.id);
      setSelectedRun(detail);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load sync run detail");
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Sync History</h1>
        <p className="page-description">
          Review persisted manual sync runs and inspect which workflows were created, updated, skipped, or blocked
        </p>
      </div>

      {error ? (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="empty-state card">
          <div className="empty-state__icon">⏳</div>
          <p className="empty-state__text">Loading sync history...</p>
        </div>
      ) : (
        <>
          <SyncHistoryTable
            items={history}
            selectedId={selectedRun?.id}
            onSelect={handleSelect}
          />

          {selectedRun ? (
            <div className="card" style={{ marginTop: 20, padding: 24 }}>
              <div className="section-title">Selected Run</div>
              <p className="section-subtitle">
                Run {selectedRun.id} • {selectedRun.status} • {formatTimestamp(selectedRun.started_at)}
              </p>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                  gap: 12,
                  marginTop: 18,
                }}
              >
                <HistorySummary
                  label="Created"
                  value={selectedRun.summary.created}
                  tone="var(--c-green)"
                />
                <HistorySummary
                  label="Updated"
                  value={selectedRun.summary.updated}
                  tone="var(--c-blue)"
                />
                <HistorySummary
                  label="Skipped"
                  value={selectedRun.summary.skipped}
                  tone="var(--c-slate)"
                />
                <HistorySummary
                  label="Blocked"
                  value={selectedRun.summary.unsupported + selectedRun.summary.conflicts}
                  tone="var(--c-amber)"
                />
                <HistorySummary
                  label="Failed"
                  value={selectedRun.summary.failed}
                  tone="var(--c-red)"
                />
              </div>

              {selectedRun.audit ? (
                <div style={{ display: "grid", gap: 8, marginTop: 18 }}>
                  {selectedRun.audit.source_db?.display_url ? (
                    <div style={{ fontSize: "0.8rem", color: "var(--c-text-tertiary)" }}>
                      Source DB:{" "}
                      <span style={{ fontFamily: "var(--font-mono)" }}>
                        {selectedRun.audit.source_db.display_url}
                      </span>
                    </div>
                  ) : null}
                  {selectedRun.audit.target_db?.display_url ? (
                    <div style={{ fontSize: "0.8rem", color: "var(--c-text-tertiary)" }}>
                      Target DB:{" "}
                      <span style={{ fontFamily: "var(--font-mono)" }}>
                        {selectedRun.audit.target_db.display_url}
                      </span>
                    </div>
                  ) : null}
                  {selectedRun.audit.last_error ? (
                    <div className="alert alert--error">{selectedRun.audit.last_error}</div>
                  ) : null}
                </div>
              ) : null}

              <div style={{ marginTop: 20 }}>
                <div className="section-title" style={{ fontSize: "0.95rem", marginBottom: 12 }}>
                  Workflow Changes
                </div>
                <SyncVisualBoard
                  items={selectedRun.items}
                  emptyMessage="No workflow changes were persisted for this run"
                  emptyIcon="📭"
                />
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
}

function HistorySummary({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-card__value" style={{ color: tone }}>
        {value}
      </div>
      <div className="stat-card__label">{label}</div>
    </div>
  );
}
