import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import StepNavigation from "../components/layout/StepNavigation";
import ConversionReportView from "../components/result/ConversionReport";
import DownloadButton from "../components/result/DownloadButton";
import DirectWriteButton from "../components/result/DirectWriteButton";
import WarningList from "../components/result/WarningList";
import { useWorkflowStore } from "../store/workflowStore";
import { getConversion } from "../api/conversion";

export default function ResultPage() {
  const { conversionId } = useParams();
  const {
    conversionId: storedConversionId,
    conversionDetail,
    conversionReport,
    setConversion,
  } = useWorkflowStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeDetail =
    conversionDetail && storedConversionId === conversionId ? conversionDetail : null;
  const activeReport =
    activeDetail?.report || (storedConversionId === conversionId ? conversionReport : null);

  useEffect(() => {
    if (!conversionId || activeDetail) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    getConversion(conversionId)
      .then((result) => {
        if (!cancelled) {
          setConversion(result.conversion_id, result.report, result);
        }
      })
      .catch((e: any) => {
        if (!cancelled) {
          setError(e?.response?.data?.detail || e?.message || "Failed to load conversion");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeDetail, conversionId, setConversion]);

  if (loading && !activeReport) {
    return (
      <div className="fade-in">
        <StepNavigation currentStep={3} />
        <div className="empty-state">
          <div className="empty-state__icon">⏳</div>
          <p className="empty-state__text">Loading export result...</p>
        </div>
      </div>
    );
  }

  if ((!activeReport || !conversionId) && error) {
    return (
      <div className="fade-in">
        <StepNavigation currentStep={3} />
        <div className="empty-state">
          <div className="empty-state__icon">⚠️</div>
          <p className="empty-state__text">{error}</p>
        </div>
      </div>
    );
  }

  if (!activeReport || !conversionId) {
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
          Workflow "{activeReport.workflow_name}" — conversion complete
        </p>
      </div>

      <ConversionReportView report={activeReport} />

      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

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

      <WarningList results={activeReport.node_results} />
    </div>
  );
}
