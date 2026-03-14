import { useParams } from "@umijs/max";
import StepNavigation from "../components/layout/StepNavigation";
import MappingTable from "../components/mapping/MappingTable";
import { useWorkflowStore } from "../store/workflowStore";

export default function MappingPage() {
  const { workflowId } = useParams();
  const { conversionReport } = useWorkflowStore();

  return (
    <div className="fade-in">
      <StepNavigation currentStep={1} />

      <div className="page-header">
        <h1 className="page-title">Node Mapping</h1>
        <p className="page-description">
          Workflow <span style={{ fontFamily: "var(--font-mono)", color: "var(--c-accent)" }}>{workflowId}</span>
        </p>
      </div>

      {conversionReport ? (
        <MappingTable results={conversionReport.node_results} />
      ) : (
        <div className="empty-state">
          <div className="empty-state__icon">🔗</div>
          <p className="empty-state__text">No conversion data available. Upload a workflow first.</p>
        </div>
      )}
    </div>
  );
}
