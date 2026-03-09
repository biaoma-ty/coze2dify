import { useState } from "react";

interface Props {
  label: string;
  workflowLabel?: string;
  onTest: (url: string) => void | Promise<void>;
  onSubmit?: (params: { url: string; workflowId: string }) => void | Promise<void>;
  submitLabel?: string;
}

export default function DbConnectionConfig({
  label,
  workflowLabel = "Workflow ID",
  onTest,
  onSubmit,
  submitLabel = "Fetch Workflow",
}: Props) {
  const [url, setUrl] = useState("");
  const [workflowId, setWorkflowId] = useState("");

  return (
    <div className="card card--elevated" style={{ padding: 24 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: url ? "var(--c-amber)" : "var(--c-border)",
            }}
          />
          <span className="section-title" style={{ fontSize: "0.9rem" }}>{label} Database</span>
        </div>

        <div>
          <label className="label">Connection URL</label>
          <input
            className="input input-mono"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="postgresql://user:pass@host:5432/dbname"
          />
        </div>

        {onSubmit && (
          <div>
            <label className="label">{workflowLabel}</label>
            <input
              className="input input-mono"
              value={workflowId}
              onChange={(e) => setWorkflowId(e.target.value)}
              placeholder="1"
            />
          </div>
        )}

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button
            className={`btn ${url ? "btn-secondary" : "btn-ghost"}`}
            onClick={() => onTest(url)}
            disabled={!url}
            style={{ alignSelf: "flex-start" }}
          >
            🔌 Test Connection
          </button>
          {onSubmit && (
            <button
              className={`btn ${url && workflowId ? "btn-primary" : "btn-secondary"}`}
              onClick={() => onSubmit({ url, workflowId })}
              disabled={!url || !workflowId}
              style={{ alignSelf: "flex-start" }}
            >
              ⚡ {submitLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
