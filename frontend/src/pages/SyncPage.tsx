import { useEffect, useState } from "react";
import SyncHistoryTable from "../components/sync/SyncHistoryTable";
import {
  executeManualSync,
  getSyncConfig,
  getSyncHistoryDetail,
  listSyncHistory,
  saveSyncConfig,
  testSyncConnections,
} from "../api/sync";
import type {
  SyncConfig,
  SyncConfigInput,
  SyncConnectionResult,
  SyncHistoryEntry,
  SyncRunDetail,
  SyncRunItem,
  SyncSummary,
} from "../types/sync";

const DEFAULT_FORM: SyncConfigInput = {
  name: "Manual Sync",
  coze_db_type: "postgresql",
  coze_db_url: "",
  dify_db_url: "",
  sync_mode: "manual",
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
  const [connections, setConnections] = useState<SyncConnectionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  useEffect(() => {
    void loadPage();
  }, []);

  const loadPage = async () => {
    setLoading(true);
    setError("");
    try {
      const [config, historyItems] = await Promise.all([getSyncConfig(), listSyncHistory()]);
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

  const updateField = (field: keyof SyncConfigInput, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
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

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setInfo("");
    try {
      const saved = await saveSyncConfig(form);
      setForm(toInput(saved));
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
      setSelectedRun(run);
      await refreshHistory(run.id);
      setInfo("Manual sync run completed.");
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Manual sync failed");
    } finally {
      setRunning(false);
    }
  };

  const handleSelectRun = async (entry: SyncHistoryEntry) => {
    setError("");
    try {
      const detail = await getSyncHistoryDetail(entry.id);
      setSelectedRun(detail);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load sync run details");
    }
  };

  const disabled = !form.coze_db_url.trim() || !form.dify_db_url.trim();
  const summary = selectedRun?.summary || EMPTY_SUMMARY;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Manual Sync</h1>
        <p className="page-description">
          Run a persisted Coze to Dify sync from the UI using the existing conversion and Dify write path
        </p>
      </div>

      {error && <div className="alert alert--error" style={{ marginBottom: 16 }}>{error}</div>}
      {info && <div className="alert alert--success" style={{ marginBottom: 16 }}>{info}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
        <div className="card card--elevated" style={{ padding: 24 }}>
          <div className="section-title">Sync Configuration</div>
          <p className="section-subtitle">Minimum MVP input: Coze source database and Dify target database.</p>

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
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 20 }}>
            <button className="btn btn-secondary" onClick={handleSave} disabled={disabled || saving}>
              {saving ? "Saving..." : "Save Config"}
            </button>
            <button className="btn btn-ghost" onClick={handleTest} disabled={disabled || testing}>
              {testing ? "Testing..." : "Test Connections"}
            </button>
            <button className="btn btn-primary" onClick={handleRun} disabled={disabled || running}>
              {running ? "Running..." : "Run Manual Sync"}
            </button>
          </div>

          {connections && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 20 }}>
              <ConnectionCard
                label="Coze"
                result={connections.coze_db}
              />
              <ConnectionCard
                label="Dify"
                result={connections.dify_db}
              />
            </div>
          )}
        </div>

        <div className="card" style={{ padding: 24 }}>
          <div className="section-title">Current Run Summary</div>
          <p className="section-subtitle">
            {selectedRun
              ? `Run ${selectedRun.id} • ${formatTimestamp(selectedRun.started_at)}`
              : "No manual sync has been executed yet."}
          </p>

          {loading ? (
            <div className="empty-state" style={{ paddingBottom: 0 }}>
              <div className="empty-state__icon">⏳</div>
              <p className="empty-state__text">Loading sync history...</p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12, marginTop: 20 }}>
              <SummaryCard label="Created" value={summary.created} tone="green" />
              <SummaryCard label="Updated" value={summary.updated} tone="blue" />
              <SummaryCard label="Skipped" value={summary.skipped} tone="slate" />
              <SummaryCard label="Unsupported" value={summary.unsupported} tone="amber" />
              <SummaryCard label="Conflicts" value={summary.conflicts} tone="amber" />
              <SummaryCard label="Failed" value={summary.failed} tone="red" />
            </div>
          )}

          {selectedRun && (
            <div style={{ marginTop: 20 }}>
              <div
                className={`alert ${
                  selectedRun.status === "completed"
                    ? "alert--success"
                    : selectedRun.status === "failed"
                      ? "alert--error"
                      : "alert--warning"
                }`}
              >
                Status: <strong>{selectedRun.status}</strong>
                {selectedRun.completed_at && ` • Completed ${formatTimestamp(selectedRun.completed_at)}`}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 28 }}>
        <div className="section-title" style={{ marginBottom: 12 }}>Run Details</div>
        <RunItemsTable items={selectedRun?.items || []} />
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
    cron_expression: config.cron_expression,
  };
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Pending";
  }
  return new Date(value).toLocaleString();
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

function RunItemsTable({ items }: { items: SyncRunItem[] }) {
  if (items.length === 0) {
    return (
      <div className="empty-state card" style={{ borderStyle: "dashed" }}>
        <div className="empty-state__icon">🧭</div>
        <p className="empty-state__text">No sync run selected yet</p>
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
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
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
            </tr>
          ))}
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
