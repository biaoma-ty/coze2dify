import SyncDashboard from "../components/sync/SyncDashboard";
import SyncConfigForm from "../components/sync/SyncConfigForm";

export default function SyncPage() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Sync Management</h1>
        <p className="page-description">
          Configure bidirectional sync between Coze and Dify databases
        </p>
      </div>

      <SyncDashboard />

      <div style={{ marginTop: 32 }}>
        <div className="section-title" style={{ marginBottom: 16 }}>Database Connections</div>
        <SyncConfigForm />
      </div>

      <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
        <button className="btn btn-primary" onClick={() => alert("Sync execution not yet implemented")}>
          ⚡ Execute Sync Now
        </button>
        <button className="btn btn-secondary" onClick={() => alert("Schedule not yet implemented")}>
          🕐 Schedule Sync
        </button>
      </div>
    </div>
  );
}
