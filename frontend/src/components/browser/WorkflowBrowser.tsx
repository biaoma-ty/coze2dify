import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { usePlatformStore } from "../../store/platformStore";
import { useWorkflowStore } from "../../store/workflowStore";
import {
  listCozeWorkflows,
  listDifyApps,
} from "../../api/platform";
import { convertWorkflowFromApi } from "../../api/conversion";
import type { CozeWorkflowItem, DifyAppItem } from "../../types/platform";

export default function WorkflowBrowser() {
  const navigate = useNavigate();
  const {
    activeTab,
    setActiveTab,
    cozeConnected,
    cozeToken,
    cozeApiBase,
    cozeWorkspaces,
    cozeSelectedSpace,
    setCozeSelectedSpace,
    cozeWorkflows,
    setCozeWorkflows,
    difyConnected,
    difyApiBase,
    difyApiKey,
    difyApps,
    setDifyApps,
    difySelectedAppId,
    setDifySelectedApp,
  } = usePlatformStore();
  const { setConversion, setSourceMethod } = useWorkflowStore();

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState("");

  const connected = activeTab === "coze" ? cozeConnected : difyConnected;

  /* ── fetch on tab/space change ─────────────── */

  const loadCozeWorkflows = async (spaceId: string) => {
    if (!spaceId || !cozeToken) return;
    setLoading(true);
    try {
      const wf = await listCozeWorkflows(cozeToken, cozeApiBase, spaceId);
      setCozeWorkflows(wf);
    } catch {
      setCozeWorkflows([]);
    } finally {
      setLoading(false);
    }
  };

  const loadDifyApps = async () => {
    if (!difyApiBase || !difyApiKey) return;
    setLoading(true);
    try {
      const apps = await listDifyApps(difyApiBase, difyApiKey);
      setDifyApps(apps);
    } catch {
      setDifyApps([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "coze" && cozeConnected && cozeSelectedSpace) {
      loadCozeWorkflows(cozeSelectedSpace);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, cozeSelectedSpace, cozeConnected]);

  useEffect(() => {
    if (activeTab === "dify" && difyConnected) {
      loadDifyApps();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, difyConnected]);

  /* ── filtered list ─────────────────────────── */

  const filteredCoze = useMemo(() => {
    const q = search.toLowerCase();
    return cozeWorkflows.filter(
      (w) => w.bot_name.toLowerCase().includes(q) || w.bot_id.toLowerCase().includes(q),
    );
  }, [cozeWorkflows, search]);

  const filteredDify = useMemo(() => {
    const q = search.toLowerCase();
    return difyApps.filter(
      (a) => a.name.toLowerCase().includes(q) || a.app_id.toLowerCase().includes(q),
    );
  }, [difyApps, search]);

  /* ── render ────────────────────────────────── */

  return (
    <div className="card fade-in fade-in-2" style={{ overflow: "hidden" }}>
      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 20px",
          borderBottom: "1px solid var(--c-border-subtle)",
        }}
      >
        <div className="tab-bar">
          <button
            className={`tab-btn ${activeTab === "coze" ? "tab-btn--active" : ""}`}
            onClick={() => setActiveTab("coze")}
          >
            Coze Workflows
          </button>
          <button
            className={`tab-btn ${activeTab === "dify" ? "tab-btn--active" : ""}`}
            onClick={() => setActiveTab("dify")}
          >
            Dify Apps
          </button>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            className="input"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 220, padding: "7px 12px", fontSize: "0.8rem" }}
          />
          <button
            className="btn btn-ghost"
            style={{ padding: "7px 12px", fontSize: "0.78rem" }}
            onClick={() => {
              if (activeTab === "coze") loadCozeWorkflows(cozeSelectedSpace);
              else loadDifyApps();
            }}
            disabled={!connected || loading}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Coze workspace selector */}
      {activeTab === "coze" && cozeConnected && cozeWorkspaces.length > 0 && (
        <div
          style={{
            padding: "12px 20px",
            borderBottom: "1px solid var(--c-border-subtle)",
            background: "var(--c-surface-0)",
          }}
        >
          <label className="label" style={{ marginBottom: 4 }}>
            Workspace
          </label>
          <select
            className="input"
            value={cozeSelectedSpace}
            onChange={(e) => setCozeSelectedSpace(e.target.value)}
            style={{ maxWidth: 360 }}
          >
            <option value="">Select workspace...</option>
            {cozeWorkspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name} ({ws.id})
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Content */}
      <div style={{ padding: 20 }}>
        {actionError && (
          <div className="alert alert--error" style={{ marginBottom: 16 }}>
            {actionError}
          </div>
        )}

        {!connected ? (
          <EmptyState icon="🔗" text={`Connect to ${activeTab === "coze" ? "Coze" : "Dify"} above to browse workflows`} />
        ) : loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <span className="spinner" />
          </div>
        ) : activeTab === "coze" ? (
          filteredCoze.length === 0 ? (
            <EmptyState
              icon="📂"
              text={cozeSelectedSpace ? "No workflows found" : "Select a workspace to list workflows"}
            />
          ) : (
            <WorkflowList items={filteredCoze.map((w) => ({
              id: w.workflow_id || w.bot_id,
              name: w.bot_name,
              description: w.description,
              meta: w.publish_time,
              selected: false,
              actionLabel: "Migrate →",
            }))} onSelect={async (item) => {
              setLoading(true);
              setActionError("");
              try {
                const result = await convertWorkflowFromApi({
                  access_token: cozeToken,
                  api_base: cozeApiBase,
                  workflow_id: item.id,
                });
                setSourceMethod("api");
                setConversion(result.conversion_id, result.report);
                navigate(`/diff/${result.conversion_id}`);
              } catch (e: any) {
                setActionError(
                  e?.response?.data?.detail ||
                    e?.message ||
                    "Failed to fetch workflow from Coze API. If this item is a bot record, use Upload > Coze API with the workflow ID.",
                );
              } finally {
                setLoading(false);
              }
            }} />
          )
        ) : filteredDify.length === 0 ? (
          <EmptyState icon="📂" text="No apps found" />
        ) : (
          <WorkflowList items={filteredDify.map((a) => ({
            id: a.app_id,
            name: a.name,
            description: a.description,
            meta: `${a.mode} · ${a.updated_at}`,
            selected: difySelectedAppId === a.app_id,
            actionLabel: difySelectedAppId === a.app_id ? "Selected" : "Use as Target",
          }))} onSelect={(item) => {
            setActionError("");
            setDifySelectedApp(item.id);
          }} />
        )}
      </div>
    </div>
  );
}

/* ── helpers ──────────────────────────────────── */

function EmptyState({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="empty-state" style={{ padding: "40px 20px" }}>
      <div className="empty-state__icon">{icon}</div>
      <p className="empty-state__text">{text}</p>
    </div>
  );
}

interface WorkflowListItem {
  id: string;
  name: string;
  description: string;
  meta: string;
  selected: boolean;
  actionLabel: string;
}

function WorkflowList({
  items,
  onSelect,
}: {
  items: WorkflowListItem[];
  onSelect: (item: WorkflowListItem) => void | Promise<void>;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map((item) => (
        <div
          key={item.id}
          className="card card--interactive"
          style={{
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            cursor: "pointer",
            borderColor: item.selected ? "var(--c-accent)" : undefined,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.88rem",
                color: "var(--c-text-primary)",
                marginBottom: 3,
              }}
            >
              {item.name}
            </div>
            <div
              style={{
                display: "flex",
                gap: 12,
                alignItems: "center",
                fontSize: "0.72rem",
                color: "var(--c-text-tertiary)",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  background: "var(--c-surface-3)",
                  padding: "2px 8px",
                  borderRadius: 4,
                }}
              >
                {item.id.length > 16 ? item.id.slice(0, 16) + "…" : item.id}
              </span>
              {item.description && (
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.description}
                </span>
              )}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {item.meta && (
              <span
                style={{
                  fontSize: "0.7rem",
                  color: "var(--c-text-tertiary)",
                  fontFamily: "var(--font-mono)",
                  whiteSpace: "nowrap",
                }}
              >
                {item.meta}
              </span>
            )}
            <button
              className={item.selected ? "btn btn-secondary" : "btn btn-primary"}
              style={{ padding: "6px 16px", fontSize: "0.75rem" }}
              onClick={(e) => {
                e.stopPropagation();
                void onSelect(item);
              }}
            >
              {item.actionLabel}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
