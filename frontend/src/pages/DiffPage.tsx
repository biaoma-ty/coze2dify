import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ConversionVisualBoard from "../components/diff/ConversionVisualBoard";
import StepNavigation from "../components/layout/StepNavigation";
import MappingTable from "../components/mapping/MappingTable";
import ConversionReportView from "../components/result/ConversionReport";
import { useWorkflowStore } from "../store/workflowStore";
import { getConversion } from "../api/conversion";

export default function DiffPage() {
  const { conversionId } = useParams();
  const navigate = useNavigate();
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
        <StepNavigation currentStep={2} />
        <div className="empty-state">
          <div className="empty-state__icon">⏳</div>
          <p className="empty-state__text">Loading conversion preview...</p>
        </div>
      </div>
    );
  }

  if (error && !activeReport) {
    return (
      <div className="fade-in">
        <StepNavigation currentStep={2} />
        <div className="empty-state">
          <div className="empty-state__icon">⚠️</div>
          <p className="empty-state__text">{error}</p>
        </div>
      </div>
    );
  }

  if (!activeReport) {
    return (
      <div className="fade-in">
        <StepNavigation currentStep={2} />
        <div className="empty-state">
          <div className="empty-state__icon">👁</div>
          <p className="empty-state__text">No data. Upload a workflow first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <StepNavigation currentStep={2} />

      <div className="page-header">
        <h1 className="page-title">Conversion Preview</h1>
        <p className="page-description">
          Review the mapping results before exporting
        </p>
      </div>

      <ConversionReportView report={activeReport} />

      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 12 }}>Visual Diff</div>
        <p className="section-subtitle">
          Grouped by mapping outcome, with persisted source and target graph summaries.
        </p>
        <div style={{ marginTop: 16 }}>
          <ConversionVisualBoard
            report={activeReport}
            sourceGraph={activeDetail?.source_graph || null}
            targetGraph={activeDetail?.target_graph || null}
          />
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 16 }}>Node Details</div>
        <MappingTable results={activeReport.node_results} />
      </div>

      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
        <button className="btn btn-primary" onClick={() => navigate(`/result/${conversionId}`)}>
          Continue to Export →
        </button>
        <button className="btn btn-ghost" onClick={() => navigate("/")}>
          ← Start Over
        </button>
      </div>
    </div>
  );
}
