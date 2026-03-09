import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import MappingPage from "./pages/MappingPage";
import DiffPage from "./pages/DiffPage";
import ResultPage from "./pages/ResultPage";
import SyncPage from "./pages/SyncPage";
import SyncHistoryPage from "./pages/SyncHistoryPage";
import BrowsePage from "./pages/BrowsePage";
import ConversionHistoryPage from "./pages/ConversionHistoryPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/browse" element={<BrowsePage />} />
      <Route path="/mapping/:workflowId" element={<MappingPage />} />
      <Route path="/diff/:conversionId" element={<DiffPage />} />
      <Route path="/result/:conversionId" element={<ResultPage />} />
      <Route path="/sync" element={<SyncPage />} />
      <Route path="/sync/history" element={<SyncHistoryPage />} />
      <Route path="/history" element={<ConversionHistoryPage />} />
    </Routes>
  );
}
