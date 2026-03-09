import { useSyncStore } from "../../store/conversionStore";

export default function SyncDashboard() {
  const { syncStatus, cozeDbConnected, difyDbConnected } = useSyncStore();

  const statusColor = {
    idle: "var(--c-slate)",
    running: "var(--c-blue)",
    completed: "var(--c-green)",
    failed: "var(--c-red)",
  }[syncStatus];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
      <div className="stat-card stat-card--blue fade-in fade-in-1">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <div className="pulse-dot" style={{ background: statusColor }} />
          <span className="stat-card__label">Sync Status</span>
        </div>
        <div className="stat-card__value" style={{ color: statusColor, fontSize: "1.3rem" }}>
          {syncStatus.toUpperCase()}
        </div>
      </div>

      <div className={`stat-card ${cozeDbConnected ? "stat-card--green" : "stat-card--red"} fade-in fade-in-2`}>
        <div className="stat-card__label" style={{ marginBottom: 8 }}>Coze Database</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: cozeDbConnected ? "var(--c-green)" : "var(--c-red)",
            }}
          />
          <span style={{
            fontWeight: 700,
            fontSize: "0.9rem",
            color: cozeDbConnected ? "var(--c-green)" : "var(--c-red)",
          }}>
            {cozeDbConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      <div className={`stat-card ${difyDbConnected ? "stat-card--green" : "stat-card--red"} fade-in fade-in-3`}>
        <div className="stat-card__label" style={{ marginBottom: 8 }}>Dify Database</div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: difyDbConnected ? "var(--c-green)" : "var(--c-red)",
            }}
          />
          <span style={{
            fontWeight: 700,
            fontSize: "0.9rem",
            color: difyDbConnected ? "var(--c-green)" : "var(--c-red)",
          }}>
            {difyDbConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>
    </div>
  );
}
