import { useEffect, useState } from "react";
import { useParams } from "@umijs/max";
import { useTranslation } from "react-i18next";
import PageShell from "../components/common/PageShell";
import Skeleton from "../components/common/Skeleton";
import { getSyncHistoryDetail } from "../api/sync";
import type { SyncRunDetail } from "../types/sync";

export default function SyncRunDetailPage() {
  const { t } = useTranslation();
  const { runId } = useParams<{ runId: string }>();
  const [detail, setDetail] = useState<SyncRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;

    setLoading(true);
    setError(null);
    getSyncHistoryDetail(runId)
      .then((result) => {
        if (!cancelled) {
          setDetail(result);
        }
      })
      .catch((e: any) => {
        if (!cancelled) {
          setError(
            e?.response?.data?.detail || e?.message || "Failed to load sync run detail",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [runId]);

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.sync"), to: "/sync" },
        { label: t("sync.history.title"), to: "/history" },
        { label: runId ? `Run ${runId.slice(0, 8)}...` : t("sync.history.runDetails") },
      ]}
      title={t("sync.history.runDetails")}
      subtitle={runId ? `Run ID: ${runId}` : undefined}
    >
      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ display: "grid", gap: 16 }}>
          <Skeleton variant="card" count={2} />
          <Skeleton variant="row" count={5} />
        </div>
      )}

      {!loading && detail && (
        <>
          {/* Summary Stats */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
              gap: 12,
              marginBottom: 24,
            }}
          >
            <div className="stat-card stat-card--green">
              <div className="stat-card__value">{detail.summary.created}</div>
              <div className="stat-card__label">{t("sync.summary.created")}</div>
            </div>
            <div className="stat-card stat-card--blue">
              <div className="stat-card__value">{detail.summary.updated}</div>
              <div className="stat-card__label">{t("sync.summary.updated")}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card__value">{detail.summary.skipped}</div>
              <div className="stat-card__label">{t("sync.summary.skipped")}</div>
            </div>
            <div className="stat-card stat-card--amber">
              <div className="stat-card__value">{detail.summary.conflicts}</div>
              <div className="stat-card__label">{t("sync.summary.conflicts")}</div>
            </div>
            <div className="stat-card stat-card--red">
              <div className="stat-card__value">{detail.summary.failed}</div>
              <div className="stat-card__label">{t("sync.summary.failed")}</div>
            </div>
          </div>

          {/* Status and Audit Info */}
          <div className="card" style={{ padding: 20, marginBottom: 20 }}>
            <div style={{ display: "grid", gap: 8 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: "0.85rem", color: "var(--c-text-tertiary)" }}>
                  Status:
                </span>
                <span className={`badge badge--${detail.status === "completed" ? "mapped" : detail.status === "failed" ? "unmappable" : "partial"}`}>
                  {detail.status}
                </span>
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--c-text-tertiary)" }}>
                {t("sync.config.configName")}: {detail.sync_config_name || "Manual Sync"}
              </div>
              {detail.started_at && (
                <div style={{ fontSize: "0.85rem", color: "var(--c-text-tertiary)" }}>
                  Started: {new Date(detail.started_at).toLocaleString()}
                </div>
              )}
              {detail.completed_at && (
                <div style={{ fontSize: "0.85rem", color: "var(--c-text-tertiary)" }}>
                  Completed: {new Date(detail.completed_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>

          {/* Workflow Items */}
          {detail.items.length > 0 && (
            <div className="card" style={{ padding: 20 }}>
              <div className="section-title" style={{ marginBottom: 16 }}>
                Workflow Changes
              </div>
              <div className="table-wrap">
                <table className="c2d-table">
                  <thead>
                    <tr>
                      <th>Workflow</th>
                      <th>Action</th>
                      <th>Status</th>
                      <th>Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.items.map((item, index) => (
                      <tr key={`${item.source_workflow_id}-${index}`}>
                        <td>
                          <div style={{ display: "grid", gap: 4 }}>
                            <span style={{ fontWeight: 600, color: "var(--c-text-primary)" }}>
                              {item.source_workflow_name}
                            </span>
                            <span style={{ fontSize: "0.76rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
                              {item.source_workflow_id}
                            </span>
                          </div>
                        </td>
                        <td>
                          <span className="badge badge--skipped">{item.action}</span>
                        </td>
                        <td>
                          <span className={`badge badge--${item.status === "created" || item.status === "updated" ? "mapped" : item.status === "failed" ? "unmappable" : "partial"}`}>
                            {item.status}
                          </span>
                        </td>
                        <td style={{ fontSize: "0.82rem", color: "var(--c-text-secondary)" }}>
                          {item.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !detail && !error && (
        <div className="empty-state card" style={{ borderStyle: "dashed" }}>
          <p className="empty-state__text">{t("sync.history.selectRun")}</p>
        </div>
      )}
    </PageShell>
  );
}
