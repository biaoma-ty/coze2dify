import { useState, useEffect } from "react";
import { usePlatformStore } from "../../store/platformStore";
import { getDevModeStatus, devModeAutoConnect } from "../../api/platform";

export default function DevModeBanner() {
  const {
    devModeEnabled,
    detectedCoze,
    detectedDify,
    setDevMode,
    setDifyDb,
    setCozeDb,
  } = usePlatformStore();

  const [collapsed, setCollapsed] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectResult, setConnectResult] = useState<string | null>(null);

  /* ── check dev mode on mount ───────────────── */

  useEffect(() => {
    (async () => {
      try {
        const status = await getDevModeStatus();
        setDevMode(status.enabled, status.detected.coze, status.detected.dify);
      } catch {
        // silently ignore — dev mode just won't show
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!devModeEnabled) return null;

  const totalDetected = detectedCoze.length + detectedDify.length;
  if (totalDetected === 0) return null;

  const handleAutoConnect = async () => {
    setConnecting(true);
    setConnectResult(null);
    try {
      const result = await devModeAutoConnect();
      const parts: string[] = [];

      for (const d of result.results.dify) {
        if (d.db_connected) {
          setDifyDb(d.db_url, true);
          parts.push(`Dify DB ✓`);
        }
      }
      for (const c of result.results.coze) {
        if (c.db_connected) {
          setCozeDb(c.db_url, true);
          parts.push(`Coze DB ✓`);
        }
      }

      setConnectResult(parts.length > 0 ? parts.join(" · ") : "No services could be connected");
    } catch {
      setConnectResult("Connection failed");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div
      className="fade-in"
      style={{
        background: "var(--c-amber-dim)",
        border: "1px solid #f59e0b30",
        borderRadius: "var(--radius-md)",
        marginBottom: 20,
        overflow: "hidden",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 18px",
          cursor: "pointer",
        }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="badge" style={{ background: "var(--c-amber)", color: "#000", fontWeight: 800 }}>
            DEV
          </span>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--c-amber)" }}>
            Local Deployment Detected
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--c-text-tertiary)" }}>
            {totalDetected} service{totalDetected !== 1 ? "s" : ""} found
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {!collapsed && (
            <button
              className="btn btn-primary"
              style={{ padding: "6px 14px", fontSize: "0.75rem" }}
              onClick={(e) => {
                e.stopPropagation();
                handleAutoConnect();
              }}
              disabled={connecting}
            >
              {connecting && <span className="spinner" />}
              One-Click Connect
            </button>
          )}
          <span
            style={{
              fontSize: "0.7rem",
              color: "var(--c-text-tertiary)",
              transition: "transform 0.2s",
              transform: collapsed ? "rotate(-90deg)" : "rotate(0deg)",
            }}
          >
            ▼
          </span>
        </div>
      </div>

      {/* Detail body */}
      {!collapsed && (
        <div
          style={{
            padding: "0 18px 14px",
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {detectedDify.map((svc, i) => (
            <ServiceRow key={`dify-${i}`} label="Dify" svc={svc} />
          ))}
          {detectedCoze.map((svc, i) => (
            <ServiceRow key={`coze-${i}`} label="Coze Studio" svc={svc} />
          ))}

          {connectResult && (
            <div
              style={{
                fontSize: "0.78rem",
                fontWeight: 600,
                color: connectResult.includes("✓") ? "var(--c-green)" : "var(--c-red)",
                marginTop: 4,
              }}
            >
              {connectResult}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ServiceRow({ label, svc }: { label: string; svc: { path: string; db_url: string; api_url: string } }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        fontSize: "0.75rem",
        color: "var(--c-text-secondary)",
        background: "rgba(0,0,0,0.15)",
        borderRadius: 6,
        padding: "8px 12px",
      }}
    >
      <span style={{ fontWeight: 700, color: "var(--c-amber)", minWidth: 90 }}>{label}</span>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--c-text-tertiary)" }}>
        {svc.path}
      </span>
      {svc.db_url && (
        <span
          className="badge badge--mapped"
          style={{ padding: "2px 8px", fontSize: "0.6rem" }}
        >
          DB
        </span>
      )}
      {svc.api_url && (
        <span
          className="badge badge--partial"
          style={{ padding: "2px 8px", fontSize: "0.6rem" }}
        >
          API
        </span>
      )}
    </div>
  );
}
