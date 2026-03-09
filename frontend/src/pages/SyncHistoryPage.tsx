import SyncHistoryTable from "../components/sync/SyncHistoryTable";

export default function SyncHistoryPage() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">Sync History</h1>
        <p className="page-description">
          View past synchronization runs and their results
        </p>
      </div>

      <SyncHistoryTable items={[]} />
    </div>
  );
}
