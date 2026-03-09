import { useState } from "react";

interface Props {
  onSubmit: (params: { accessToken: string; workflowId: string; apiBase: string }) => void;
}

export default function CozeApiConfig({ onSubmit }: Props) {
  const [token, setToken] = useState("");
  const [workflowId, setWorkflowId] = useState("");
  const [apiBase, setApiBase] = useState("https://api.coze.com");
  const ready = Boolean(token && workflowId && apiBase);

  return (
    <div className="card card--elevated" style={{ padding: 28 }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <label className="label">API Base</label>
          <input
            className="input input-mono"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
            placeholder="https://api.coze.com"
          />
        </div>

        <div>
          <label className="label">Coze Access Token</label>
          <input
            className="input input-mono"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="pat_xxxxxxxxxxxxx"
          />
        </div>

        <div>
          <label className="label">Workflow ID</label>
          <input
            className="input input-mono"
            value={workflowId}
            onChange={(e) => setWorkflowId(e.target.value)}
            placeholder="7xxxxxxxxxxxxx"
          />
        </div>

        <button
          className={`btn ${ready ? "btn-primary" : "btn-secondary"}`}
          onClick={() => onSubmit({ accessToken: token, workflowId, apiBase })}
          disabled={!ready}
          style={{ alignSelf: "flex-start" }}
        >
          ⚡ Fetch Workflow
        </button>
      </div>
    </div>
  );
}
