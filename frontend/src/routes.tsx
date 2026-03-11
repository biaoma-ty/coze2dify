import { Routes, Route, Navigate, useParams } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import MigratePage from "./pages/MigratePage";
import BrowsePage from "./pages/BrowsePage";
import DiffPage from "./pages/DiffPage";
import ResultPage from "./pages/ResultPage";
import SyncPage from "./pages/SyncPage";
import SyncConfigPage from "./pages/SyncConfigPage";
import SyncHistoryPage from "./pages/SyncHistoryPage";
import SyncRunDetailPage from "./pages/SyncRunDetailPage";
import UnifiedHistoryPage from "./pages/UnifiedHistoryPage";
import ConversionDetailPage from "./pages/ConversionDetailPage";
import SettingsPage from "./pages/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      {/* Dashboard */}
      <Route path="/" element={<DashboardPage />} />

      {/* Migration flow */}
      <Route path="/migrate" element={<MigratePage />} />
      <Route path="/migrate/browse" element={<BrowsePage />} />
      <Route path="/migrate/diff/:conversionId" element={<DiffPage />} />
      <Route path="/migrate/result/:conversionId" element={<ResultPage />} />

      {/* Sync */}
      <Route path="/sync" element={<SyncPage />} />
      <Route path="/sync/config" element={<SyncConfigPage />} />
      <Route path="/sync/history" element={<SyncHistoryPage />} />
      <Route path="/sync/history/:runId" element={<SyncRunDetailPage />} />

      {/* Unified History */}
      <Route path="/history" element={<UnifiedHistoryPage />} />
      <Route path="/history/conversion/:conversionId" element={<ConversionDetailPage />} />

      {/* Settings */}
      <Route path="/settings" element={<SettingsPage />} />

      {/* Backward compatibility redirects */}
      <Route path="/diff/:conversionId" element={<RedirectDiff />} />
      <Route path="/result/:conversionId" element={<RedirectResult />} />
      <Route path="/mapping/:workflowId" element={<Navigate to="/migrate" replace />} />
      <Route path="/browse" element={<Navigate to="/migrate/browse" replace />} />
    </Routes>
  );
}

function RedirectDiff() {
  const { conversionId } = useParams();
  return <Navigate to={`/migrate/diff/${conversionId}`} replace />;
}

function RedirectResult() {
  const { conversionId } = useParams();
  return <Navigate to={`/migrate/result/${conversionId}`} replace />;
}
