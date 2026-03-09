import { useParams } from "react-router-dom";
import StepNavigation from "../components/layout/StepNavigation";
import ConversionReportView from "../components/result/ConversionReport";
import DownloadButton from "../components/result/DownloadButton";
import DirectWriteButton from "../components/result/DirectWriteButton";
import WarningList from "../components/result/WarningList";
import { useWorkflowStore } from "../store/workflowStore";

export default function ResultPage() {
  const { conversionId } = useParams();
  const { conversionReport } = useWorkflowStore();

  if (!conversionReport || !conversionId) {
    return (
      <div className="fade-in">
        <StepNavigation currentStep={3} />
        <div className="empty-state">
          <div className="empty-state__icon">🚀</div>
          <p className="empty-state__text">No conversion data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <StepNavigation currentStep={3} />

      <div className="page-header">
        <h1 className="page-title">Export Result</h1>
        <p className="page-description">
          Workflow "{conversionReport.workflow_name}" — conversion complete
        </p>
      </div>

      <ConversionReportView report={conversionReport} />

      {/* Actions */}
      <div
        className="card card--elevated"
        style={{
          padding: 24,
          marginTop: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div className="section-title">Export Options</div>
          <p style={{ fontSize: "0.82rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
            Download as YAML file or write directly to Dify database
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <DownloadButton conversionId={conversionId} />
          <DirectWriteButton conversionId={conversionId} />
        </div>
      </div>

      <WarningList results={conversionReport.node_results} />
    </div>
  );
}
