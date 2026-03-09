import { useState } from "react";

interface Props {
  label: string;
  onTest: (url: string) => void;
}

export default function DbConnectionConfig({ label, onTest }: Props) {
  const [url, setUrl] = useState("");

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

        <button
          className={`btn ${url ? "btn-secondary" : "btn-ghost"}`}
          onClick={() => onTest(url)}
          disabled={!url}
          style={{ alignSelf: "flex-start" }}
        >
          🔌 Test Connection
        </button>
      </div>
    </div>
  );
}
