import { useState, useRef, useEffect } from "react";
import { usePlatformStore } from "../../store/platformStore";
import { connectCozeApi, connectDifyApi } from "../../api/platform";

/* ── Reusable combo input (text + preset dropdown) ── */

const PRESETS_COZE = [
  { value: "https://api.coze.com", label: "api.coze.com — Global" },
  { value: "https://api.coze.cn", label: "api.coze.cn — China" },
];

function ComboInput({
  value,
  onChange,
  placeholder,
  presets,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  presets: { value: string; label: string }[];
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <div style={{ position: "relative" }}>
        <input
          className="input input-mono"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setOpen(true)}
          style={{ paddingRight: 36 }}
        />
        <button
          type="button"
          onClick={() => setOpen(!open)}
          style={{
            position: "absolute",
            right: 1,
            top: 1,
            bottom: 1,
            width: 34,
            background: "transparent",
            border: "none",
            color: "var(--c-text-tertiary)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.7rem",
            borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
          }}
        >
          ▾
        </button>
      </div>

      {open && presets.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: "var(--c-surface-3)",
            border: "1px solid var(--c-border)",
            borderRadius: "var(--radius-sm)",
            overflow: "hidden",
            zIndex: 20,
            boxShadow: "var(--shadow-elevated)",
          }}
        >
          {presets.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => {
                onChange(p.value);
                setOpen(false);
              }}
              style={{
                width: "100%",
                padding: "9px 14px",
                background: value === p.value ? "var(--c-accent-dim)" : "transparent",
                border: "none",
                borderBottom: "1px solid var(--c-border-subtle)",
                color: value === p.value ? "var(--c-accent)" : "var(--c-text-secondary)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.78rem",
                textAlign: "left",
                cursor: "pointer",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background =
                  value === p.value ? "var(--c-accent-dim)" : "var(--c-surface-2)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background =
                  value === p.value ? "var(--c-accent-dim)" : "transparent")
              }
            >
              {p.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PlatformConnectPanel() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 16,
      }}
    >
      <CozePanel />
      <DifyPanel />
    </div>
  );
}

/* ── Coze source panel ───────────────────────── */

function CozePanel() {
  const {
    cozeToken,
    cozeApiBase,
    cozeConnected,
    cozeWorkspaces,
    setCozeCredentials,
    setCozeConnected,
  } = usePlatformStore();

  const [token, setToken] = useState(cozeToken);
  const [apiBase, setApiBase] = useState(cozeApiBase);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleConnect = async () => {
    if (!token.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await connectCozeApi(token.trim(), apiBase);
      setCozeCredentials(token.trim(), apiBase);
      setCozeConnected(true, result.workspaces);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Connection failed");
      setCozeConnected(false, []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "var(--c-blue-dim)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
          }}
        >
          ⚡
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--c-text-primary)" }}>
            Coze Source
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)" }}>
            Connect with Personal Access Token
          </div>
        </div>
        {cozeConnected && (
          <div
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.72rem",
              color: "var(--c-green)",
            }}
          >
            <span className="pulse-dot" style={{ background: "var(--c-green)" }} />
            Connected
          </div>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div>
          <label className="label">API Base</label>
          <ComboInput
            value={apiBase}
            onChange={setApiBase}
            placeholder="https://api.coze.com"
            presets={PRESETS_COZE}
          />
        </div>
        <div>
          <label className="label">PAT Token</label>
          <input
            className="input input-mono"
            type="password"
            placeholder="pat_xxxxxxxxxxxxxxxx"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleConnect()}
          />
        </div>

        {error && <div className="alert alert--error" style={{ fontSize: "0.78rem" }}>{error}</div>}

        <button
          className={`btn ${cozeConnected ? "btn-secondary" : "btn-primary"}`}
          onClick={handleConnect}
          disabled={loading || !token.trim()}
          style={{ width: "100%" }}
        >
          {loading && <span className="spinner" />}
          {cozeConnected ? "Reconnect" : "Connect"}
        </button>

        {cozeConnected && cozeWorkspaces.length > 0 && (
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--c-text-tertiary)",
              background: "var(--c-surface-0)",
              borderRadius: 6,
              padding: "8px 12px",
            }}
          >
            <span style={{ color: "var(--c-blue)", fontWeight: 600 }}>
              {cozeWorkspaces.length}
            </span>{" "}
            workspace{cozeWorkspaces.length !== 1 ? "s" : ""} accessible
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Dify target panel ───────────────────────── */

function DifyPanel() {
  const {
    difyApiBase,
    difyApiKey,
    difyConnected,
    setDifyCredentials,
    setDifyConnected,
  } = usePlatformStore();

  const [apiBase, setApiBase] = useState(difyApiBase);
  const [apiKey, setApiKey] = useState(difyApiKey);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const handleConnect = async () => {
    if (!apiBase.trim() || !apiKey.trim()) return;
    setLoading(true);
    setError("");
    setInfo("");
    try {
      const result = await connectDifyApi(apiBase.trim(), apiKey.trim());
      setDifyCredentials(apiBase.trim(), apiKey.trim());
      setDifyConnected(true);
      if (result.total >= 0) {
        setInfo(`${result.total} app${result.total !== 1 ? "s" : ""} found (${result.mode} mode)`);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Connection failed");
      setDifyConnected(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ padding: 24 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "var(--c-accent-dim)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
          }}
        >
          🎯
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--c-text-primary)" }}>
            Dify Target
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--c-text-tertiary)" }}>
            Connect via Console API or Service API
          </div>
        </div>
        {difyConnected && (
          <div
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.72rem",
              color: "var(--c-green)",
            }}
          >
            <span className="pulse-dot" style={{ background: "var(--c-green)" }} />
            Connected
          </div>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div>
          <label className="label">Instance URL</label>
          <input
            className="input input-mono"
            placeholder="http://localhost:80"
            value={apiBase}
            onChange={(e) => setApiBase(e.target.value)}
          />
        </div>
        <div>
          <label className="label">API Key / Console Token</label>
          <input
            className="input input-mono"
            type="password"
            placeholder="app-xxxxxxxxxxxxxxxx"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleConnect()}
          />
        </div>

        {error && <div className="alert alert--error" style={{ fontSize: "0.78rem" }}>{error}</div>}

        <button
          className={`btn ${difyConnected ? "btn-secondary" : "btn-primary"}`}
          onClick={handleConnect}
          disabled={loading || !apiBase.trim() || !apiKey.trim()}
          style={{ width: "100%" }}
        >
          {loading && <span className="spinner" />}
          {difyConnected ? "Reconnect" : "Connect"}
        </button>

        {info && (
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--c-text-tertiary)",
              background: "var(--c-surface-0)",
              borderRadius: 6,
              padding: "8px 12px",
            }}
          >
            <span style={{ color: "var(--c-accent)", fontWeight: 600 }}>
              {info}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
