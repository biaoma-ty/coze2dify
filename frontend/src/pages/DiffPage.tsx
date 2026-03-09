import { useParams, useNavigate } from "react-router-dom";
import StepNavigation from "../components/layout/StepNavigation";
import MappingTable from "../components/mapping/MappingTable";
import ConversionReportView from "../components/result/ConversionReport";
import { useWorkflowStore } from "../store/workflowStore";

export default function DiffPage() {
  const { conversionId } = useParams();
  const navigate = useNavigate();
  const { conversionReport } = useWorkflowStore();

  if (!conversionReport) {
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

      <ConversionReportView report={conversionReport} />

      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 16 }}>Node Details</div>
        <MappingTable results={conversionReport.node_results} />
      </div>

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
