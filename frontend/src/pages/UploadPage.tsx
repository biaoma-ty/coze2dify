import { useState } from "react";
import { useNavigate } from "react-router-dom";
import StepNavigation from "../components/layout/StepNavigation";
import FileUpload from "../components/upload/FileUpload";
import CozeApiConfig from "../components/upload/CozeApiConfig";
import DbConnectionConfig from "../components/upload/DbConnectionConfig";
import { useWorkflowStore } from "../store/workflowStore";
import { convertWorkflow } from "../api/conversion";

type SourceTab = "file" | "api" | "database";

const tabs: { key: SourceTab; label: string; desc: string }[] = [
  { key: "file", label: "File Upload", desc: "Upload JSON or YAML" },
  { key: "api", label: "Coze API", desc: "Fetch via access token" },
  { key: "database", label: "Database", desc: "Connect directly" },
];

export default function UploadPage() {
  const [tab, setTab] = useState<SourceTab>("file");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setConversion } = useWorkflowStore();

  const handleFileSelected = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const result = await convertWorkflow(file);
      setConversion(result.conversion_id, result.report);
      navigate(`/diff/${result.conversion_id}`);
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <StepNavigation currentStep={0} />

      <div className="page-header">
        <h1 className="page-title">Import Coze Workflow</h1>
        <p className="page-description">
          Choose a data source to begin the migration pipeline
        </p>
      </div>

      {/* Tab Bar */}
      <div className="tab-bar" style={{ marginBottom: 24 }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab-btn ${tab === t.key ? "tab-btn--active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="fade-in" key={tab}>
        {tab === "file" && <FileUpload onFileSelected={handleFileSelected} />}
        {tab === "api" && <CozeApiConfig onSubmit={(t, id) => alert(`API fetch: ${id}`)} />}
        {tab === "database" && <DbConnectionConfig label="Coze" onTest={(url) => alert(`Test: ${url}`)} />}
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 20 }}>
          <div className="spinner" />
          <span style={{ color: "var(--c-accent)", fontSize: "0.85rem", fontWeight: 500 }}>
            Processing workflow...
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
