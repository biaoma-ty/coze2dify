import { useEffect, useState } from "react";
import SyncHistoryTable from "../components/sync/SyncHistoryTable";
import {
  cancelSyncSchedule,
  executeManualSync,
  getSyncConfig,
  getSyncHistoryDetail,
  getSyncStatus,
  listSyncHistory,
  previewSyncDiff,
  resolveSyncConflict,
  saveSyncConfig,
  saveSyncSchedule,
  testSyncConnections,
} from "../api/sync";
import type {
  SyncConfig,
  SyncConfigInput,
  SyncConflictStrategy,
  SyncConnectionResult,
  SyncDiffPreview,
  SyncHistoryEntry,
  SyncRunDetail,
  SyncRunItem,
  SyncStatus,
  SyncSummary,
} from "../types/sync";

const DEFAULT_FORM: SyncConfigInput = {
  name: "Manual Sync",
  coze_db_type: "postgresql",
  coze_db_url: "",
  dify_db_url: "",
  sync_mode: "manual",
  cron_expression: "",
};

const EMPTY_SUMMARY: SyncSummary = {
  created: 0,
  updated: 0,
  failed: 0,
  skipped: 0,
  unsupported: 0,
  conflicts: 0,
};

export default function SyncPage() {
  const [form, setForm] = useState<SyncConfigInput>(DEFAULT_FORM);
  const [history, setHistory] = useState<SyncHistoryEntry[]>([]);
  const [selectedRun, setSelectedRun] = useState<SyncRunDetail | null>(null);
  const [diffPreview, setDiffPreview] = useState<SyncDiffPreview | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [connections, setConnections] = useState<SyncConnectionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [running, setRunning] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [scheduling, setScheduling] = useState(false);
  const [cancellingSchedule, setCancellingSchedule] = useState(false);
  const [resolvingConflictId, setResolvingConflictId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  useEffect(() => {
    void loadPage();
  }, []);

  const loadPage = async () => {
    setLoading(true);
    setError("");
    try {
      const [config, status, historyItems] = await Promise.all([
        getSyncConfig(),
        getSyncStatus(),
        listSyncHistory(),
      ]);

      setSyncStatus(status);
      if (config) {
        setForm(toInput(config));
      }

      setHistory(historyItems);
      if (historyItems.length > 0) {
        const detail = await getSyncHistoryDetail(historyItems[0].id);
        setSelectedRun(detail);
      } else {
        setSelectedRun(null);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load sync state");
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = async () => {
    const status = await getSyncStatus();
    setSyncStatus(status);
    return status;
  };

  const refreshHistory = async (selectedId?: string) => {
    const items = await listSyncHistory();
    setHistory(items);
    if (!selectedId) {
      return;
    }
    const match = items.find((item) => item.id === selectedId);
    if (match) {
      const detail = await getSyncHistoryDetail(match.id);
      setSelectedRun(detail);
    }
  };

  const updateField = (field: keyof SyncConfigInput, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setInfo("");
    try {
      const saved = await saveSyncConfig({
        ...form,
        sync_mode: "manual",
        cron_expression: null,
      });
      setForm(toInput(saved));
      setDiffPreview(null);
      await refreshStatus();
      setInfo("Manual sync config saved.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to save sync config");
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setError("");
    setInfo("");
    try {
      const result = await testSyncConnections(form);
      setConnections(result);
      setInfo(result.coze_db.connected && result.dify_db.connected ? "Both databases are reachable." : "");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to test database connections");
    } finally {
      setTesting(false);
    }
  };

  const handlePreview = async () => {
    setPreviewing(true);
    setError("");
    setInfo("");
    try {
      const preview = await previewSyncDiff(form);
      setDiffPreview(preview);
      setForm((current) => ({
        ...current,
        config_id: preview.config_id,
      }));
      await refreshStatus();
      setInfo("Sync diff preview updated.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to preview sync diff");
    } finally {
      setPreviewing(false);
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setError("");
    setInfo("");
    try {
      const run = await executeManualSync(form);
      setForm((current) => ({
        ...current,
        config_id: run.sync_config_id,
      }));
      setDiffPreview(null);
      setSelectedRun(run);
      await Promise.all([refreshHistory(run.id), refreshStatus()]);
      setInfo("Manual sync run completed.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Manual sync failed");
    } finally {
      setRunning(false);
    }
  };

  const handleSchedule = async () => {
    const cronExpression = form.cron_expression?.trim() || "";
    if (!cronExpression) {
      setError("Cron expression is required to save a schedule.");
      return;
    }

    setScheduling(true);
    setError("");
    setInfo("");
    try {
      const { config } = await saveSyncSchedule({
        ...form,
        cron_expression: cronExpression,
        sync_mode: "scheduled",
      });
      setForm(toInput(config));
      await refreshStatus();
      setInfo("Scheduled sync saved.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to save schedule");
    } finally {
      setScheduling(false);
    }
  };

  const handleCancelSchedule = async () => {
    if (!form.config_id) {
      setError("Save a config before cancelling a schedule.");
      return;
    }

    setCancellingSchedule(true);
    setError("");
    setInfo("");
    try {
      const { config, cancelled } = await cancelSyncSchedule(form.config_id);
      setForm(toInput(config));
      await refreshStatus();
      setInfo(cancelled ? "Scheduled sync cancelled." : "No active schedule was registered for this config.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to cancel schedule");
    } finally {
      setCancellingSchedule(false);
    }
  };

  const handleResolveConflict = async (
    conflictId: string,
    strategy: SyncConflictStrategy,
  ) => {
    if (!selectedRun) {
      return;
    }

    setResolvingConflictId(conflictId);
    setError("");
    setInfo("");
    try {
      const result = await resolveSyncConflict(conflictId, {
        history_id: selectedRun.id,
        strategy,
      });
      setDiffPreview(null);
      setSelectedRun(result);
      await Promise.all([refreshHistory(result.id), refreshStatus()]);
      setInfo(
        strategy === "source_wins"
          ? "Conflict resolved by applying the source workflow."
          : strategy === "target_wins"
            ? "Conflict resolved by keeping the current Dify target."
            : "Conflict marked for manual review.",
      );
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to resolve conflict");
    } finally {
      setResolvingConflictId(null);
    }
  };

  const handleSelectRun = async (entry: SyncHistoryEntry) => {
    setError("");
    setDiffPreview(null);
    try {
      const detail = await getSyncHistoryDetail(entry.id);
      setSelectedRun(detail);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load sync run details");
    }
  };

  const disabled = !form.coze_db_url.trim() || !form.dify_db_url.trim();
  const scheduledJobs = syncStatus?.scheduled_jobs || [];
  const currentSchedule = form.config_id
    ? scheduledJobs.find((job) => job.config_id === form.config_id) || null
    : null;
  const runSummary = selectedRun?.summary || EMPTY_SUMMARY;
  const previewSummary = diffPreview?.summary || EMPTY_SUMMARY;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Sync Control</h1>
        <p className="page-description">
          Manage manual runs, cron schedules, diff previews, and conflict resolution for persisted Coze to Dify syncs
        </p>
      </div>

      {error && <div className="alert alert--error" style={{ marginBottom: 16 }}>{error}</div>}
      {info && <div className="alert alert--success" style={{ marginBottom: 16 }}>{info}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
        <div className="card card--elevated" style={{ padding: 24 }}>
          <div className="section-title">Sync Configuration</div>
          <p className="section-subtitle">
            Configure source/target databases, preview changes, run manual syncs, or persist a cron schedule.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 20 }}>
            <div>
              <label className="label">Config Name</label>
              <input
                className="input"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                placeholder="Manual Sync"
              />
            </div>

            <div>
              <label className="label">Coze Source</label>
              <input
                className="input input-mono"
                value={form.coze_db_url}
                onChange={(e) => updateField("coze_db_url", e.target.value)}
                placeholder="postgresql://user:pass@host:5432/coze"
              />
            </div>

            <div>
              <label className="label">Dify Target</label>
              <input
                className="input input-mono"
                value={form.dify_db_url}
                onChange={(e) => updateField("dify_db_url", e.target.value)}
                placeholder="postgresql://user:pass@host:5432/dify"
              />
            </div>

            <div>
              <label className="label">Cron Expression</label>
              <input
                className="input input-mono"
                value={form.cron_expression || ""}
                onChange={(e) => updateField("cron_expression", e.target.value)}
                placeholder="0 3 * * *"
              />
              <div style={{ marginTop: 6, fontSize: "0.78rem", color: "var(--c-text-tertiary)" }}>
                Use standard cron format in UTC. Example: `0 3 * * *`
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 20 }}>
            <button
              className="btn btn-secondary"
              onClick={handleSave}
              disabled={disabled || saving || Boolean(currentSchedule)}
            >
              {saving ? "Saving..." : "Save Manual Config"}
            </button>
            <button className="btn btn-ghost" onClick={handleTest} disabled={disabled || testing}>
              {testing ? "Testing..." : "Test Connections"}
            </button>
            <button className="btn btn-ghost" onClick={handlePreview} disabled={disabled || previewing}>
              {previewing ? "Previewing..." : "Preview Diff"}
            </button>
            <button className="btn btn-primary" onClick={handleRun} disabled={disabled || running}>
              {running ? "Running..." : "Run Manual Sync"}
            </button>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12 }}>
            <button className="btn btn-secondary" onClick={handleSchedule} disabled={disabled || scheduling || !form.cron_expression?.trim()}>
              {scheduling ? "Saving..." : "Save Schedule"}
            </button>
            <button className="btn btn-ghost" onClick={handleCancelSchedule} disabled={!currentSchedule || cancellingSchedule}>
              {cancellingSchedule ? "Cancelling..." : "Cancel Schedule"}
            </button>
          </div>

          {currentSchedule ? (
            <div className="alert alert--success" style={{ marginTop: 20 }}>
              <strong>Schedule Active</strong>
              <div style={{ marginTop: 4, fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                {currentSchedule.cron_expression}
              </div>
              <div style={{ marginTop: 4 }}>
                Next run: {formatTimestamp(currentSchedule.next_run_at)}
              </div>
            </div>
          ) : form.cron_expression?.trim() ? (
            <div className="alert alert--warning" style={{ marginTop: 20 }}>
              No active schedule is registered for the current config yet.
            </div>
          ) : null}

          {currentSchedule ? null : (
            <div style={{ marginTop: 12, fontSize: "0.78rem", color: "var(--c-text-tertiary)" }}>
              Updating DB URLs on an active scheduled config should go through <strong>Save Schedule</strong> so the cron
              job stays in sync with the persisted config.
            </div>
          )}

          {connections && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 20 }}>
              <ConnectionCard label="Coze" result={connections.coze_db} />
              <ConnectionCard label="Dify" result={connections.dify_db} />
            </div>
          )}
        </div>

        <div className="card" style={{ padding: 24 }}>
          <div className="section-title">Sync Status</div>
          <p className="section-subtitle">
            Review scheduler state, latest backend status, and the currently selected persisted run.
          </p>

          {loading ? (
            <div className="empty-state" style={{ paddingBottom: 0 }}>
              <div className="empty-state__icon">⏳</div>
              <p className="empty-state__text">Loading sync status...</p>
            </div>
          ) : (
            <>
              <div className={`alert ${syncStatusAlertClass(syncStatus?.status || "idle")}`} style={{ marginTop: 20 }}>
                Backend status: <strong>{syncStatus?.status || "idle"}</strong>
                {syncStatus?.history_id ? ` • Latest history ${syncStatus.history_id}` : ""}
              </div>

              <div style={{ marginTop: 20 }}>
                <div className="section-title" style={{ fontSize: "0.95rem" }}>Scheduled Jobs</div>
                {scheduledJobs.length === 0 ? (
                  <div style={{ marginTop: 8, color: "var(--c-text-tertiary)", fontSize: "0.82rem" }}>
                    No active sync schedules are currently registered in the backend process.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 12 }}>
                    {scheduledJobs.map((job) => (
                      <div key={job.job_id} className="alert alert--warning">
                        <strong>Config {job.config_id}</strong>
                        <div style={{ marginTop: 4, fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                          {job.cron_expression}
                        </div>
                        <div style={{ marginTop: 4 }}>Next run: {formatTimestamp(job.next_run_at)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ marginTop: 20 }}>
                <div className="section-title" style={{ fontSize: "0.95rem" }}>Selected Run Summary</div>
                <p className="section-subtitle">
                  {selectedRun
                    ? `Run ${selectedRun.id} • ${formatTimestamp(selectedRun.started_at)}`
                    : "No persisted sync run selected yet."}
                </p>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginTop: 16 }}>
                  <SummaryCard label="Created" value={runSummary.created} tone="green" />
                  <SummaryCard label="Updated" value={runSummary.updated} tone="blue" />
                  <SummaryCard label="Skipped" value={runSummary.skipped} tone="slate" />
                  <SummaryCard label="Unsupported" value={runSummary.unsupported} tone="amber" />
                  <SummaryCard label="Conflicts" value={runSummary.conflicts} tone="amber" />
                  <SummaryCard label="Failed" value={runSummary.failed} tone="red" />
                </div>

                {selectedRun ? (
                  <div style={{ marginTop: 16 }} className={`alert ${syncStatusAlertClass(selectedRun.status)}`}>
                    Status: <strong>{selectedRun.status}</strong>
                    {selectedRun.completed_at ? ` • Completed ${formatTimestamp(selectedRun.completed_at)}` : ""}
                  </div>
                ) : null}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: 28, padding: 24 }}>
        <div className="section-title">Diff Preview</div>
        <p className="section-subtitle">
          Preview create, update, skip, unsupported, and conflict results before running a persisted sync.
        </p>

        {diffPreview ? (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginTop: 16 }}>
              <SummaryCard label="Created" value={previewSummary.created} tone="green" />
              <SummaryCard label="Updated" value={previewSummary.updated} tone="blue" />
              <SummaryCard label="Skipped" value={previewSummary.skipped} tone="slate" />
              <SummaryCard label="Unsupported" value={previewSummary.unsupported} tone="amber" />
              <SummaryCard label="Conflicts" value={previewSummary.conflicts} tone="amber" />
              <SummaryCard label="Failed" value={previewSummary.failed} tone="red" />
            </div>

            <div style={{ marginTop: 16 }} className={`alert ${syncStatusAlertClass(diffPreview.status)}`}>
              Preview status: <strong>{diffPreview.status}</strong> • Config {diffPreview.config_id}
            </div>

            <div style={{ marginTop: 18 }}>
              <RunItemsTable
                items={diffPreview.items}
                emptyMessage="No diff preview available yet"
                emptyIcon="👁"
              />
            </div>
          </>
        ) : (
          <div className="empty-state" style={{ borderStyle: "dashed", marginTop: 16 }}>
            <div className="empty-state__icon">👁</div>
            <p className="empty-state__text">No diff preview loaded yet</p>
          </div>
        )}
      </div>

      <div style={{ marginTop: 28 }}>
        <div className="section-title" style={{ marginBottom: 12 }}>Run Details</div>
        <RunItemsTable
          items={selectedRun?.items || []}
          emptyMessage="No persisted sync run selected yet"
          emptyIcon="🧭"
          onResolveConflict={selectedRun ? handleResolveConflict : undefined}
          resolvingConflictId={resolvingConflictId}
        />
      </div>

      <div style={{ marginTop: 28 }}>
        <div className="section-title" style={{ marginBottom: 12 }}>Recent History</div>
        <SyncHistoryTable
          items={history}
          selectedId={selectedRun?.id}
          onSelect={handleSelectRun}
        />
      </div>
    </div>
  );
}

function toInput(config: SyncConfig): SyncConfigInput {
  return {
    config_id: config.id,
    name: config.name,
    coze_db_type: config.coze_db_type,
    coze_db_url: config.coze_db_url,
    dify_db_url: config.dify_db_url,
    sync_mode: config.sync_mode,
    cron_expression: config.cron_expression || "",
  };
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
}

function syncStatusAlertClass(status: SyncStatus["status"]) {
  switch (status) {
    case "completed":
      return "alert--success";
    case "failed":
      return "alert--error";
    case "partial":
    case "running":
      return "alert--warning";
    case "idle":
    default:
      return "alert--warning";
  }
}

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "green" | "blue" | "slate" | "amber" | "red";
}) {
  return (
    <div className={`stat-card stat-card--${tone}`}>
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__label">{label}</div>
    </div>
  );
}

function ConnectionCard({
  label,
  result,
}: {
  label: string;
  result: SyncConnectionResult["coze_db"];
}) {
  const tone = result.connected ? "alert--success" : "alert--error";

  return (
    <div className={`alert ${tone}`}>
      <strong>{label}</strong>
      <div style={{ marginTop: 4 }}>
        {result.connected ? "Connected" : result.error || "Connection failed"}
      </div>
    </div>
  );
}

function RunItemsTable({
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
    <div className="table-wrap">
      <table className="c2d-table">
        <thead>
          <tr>
            <th>Workflow</th>
            <th>Action</th>
            <th>Status</th>
            <th>Target</th>
            <th>Message</th>
            <th>Resolution</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => {
            const canResolve = Boolean(onResolveConflict && item.status === "conflict" && item.source_workflow_id);
            const resolving = resolvingConflictId === item.source_workflow_id;

            return (
              <tr key={`${item.source_workflow_id || "unknown"}-${index}`}>
                <td>
                  <div style={{ fontWeight: 600, color: "var(--c-text-primary)" }}>
                    {item.source_workflow_name || "Unknown workflow"}
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
                    {item.source_workflow_id || "missing-id"}
                  </div>
                </td>
                <td style={{ textTransform: "uppercase", fontSize: "0.72rem", letterSpacing: "0.06em" }}>
                  {item.action}
                </td>
                <td>
                  <span className={`badge ${runItemBadgeClass(item.status)}`}>{item.status}</span>
                </td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                  {item.target_app_id || "—"}
                </td>
                <td>{item.message}</td>
                <td style={{ minWidth: 180 }}>
                  {item.resolution ? (
                    <>
                      <div style={{ fontSize: "0.76rem", fontWeight: 600 }}>
                        {item.resolution.status}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)" }}>
                        {item.resolution.strategy}
                        {item.resolution.resolved_at ? ` • ${formatTimestamp(item.resolution.resolved_at)}` : ""}
                      </div>
                    </>
                  ) : item.status === "conflict" ? (
                    <span style={{ fontSize: "0.76rem", color: "var(--c-amber)" }}>Pending resolution</span>
                  ) : (
                    <span style={{ fontSize: "0.76rem", color: "var(--c-text-tertiary)" }}>—</span>
                  )}
                </td>
                <td style={{ minWidth: 260 }}>
                  {canResolve ? (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
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
                  ) : (
                    <span style={{ fontSize: "0.76rem", color: "var(--c-text-tertiary)" }}>
                      {item.status === "conflict" ? "Select a persisted run to resolve this conflict." : "—"}
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function runItemBadgeClass(status: SyncRunItem["status"]) {
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
