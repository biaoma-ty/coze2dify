import { useState } from "react";
import { useNavigate } from "@umijs/max";
import StepNavigation from "../components/layout/StepNavigation";
import FileUpload from "../components/upload/FileUpload";
import CozeApiConfig from "../components/upload/CozeApiConfig";
import DbConnectionConfig from "../components/upload/DbConnectionConfig";
import { useWorkflowStore } from "../store/workflowStore";
import { convertWorkflow, convertWorkflowFromApi, convertWorkflowFromDb } from "../api/conversion";
import { testDbConnection } from "../api/platform";
import { usePlatformStore } from "../store/platformStore";

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
  const { setConversion, setSourceMethod } = useWorkflowStore();
  const { setCozeCredentials, setCozeDb } = usePlatformStore();

  const handleFileSelected = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const result = await convertWorkflow(file);
      setSourceMethod("upload");
      setConversion(result.conversion_id, result.report);
      navigate(`/diff/${result.conversion_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleApiSubmit = async (params: { accessToken: string; workflowId: string; apiBase: string }) => {
    setLoading(true);
    setError(null);
    try {
      const result = await convertWorkflowFromApi({
        access_token: params.accessToken,
        workflow_id: params.workflowId,
        api_base: params.apiBase,
      });
      setCozeCredentials(params.accessToken, params.apiBase);
      setSourceMethod("api");
      setConversion(result.conversion_id, result.report);
      navigate(`/diff/${result.conversion_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "API fetch failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDbTest = async (url: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await testDbConnection("coze", url);
      if (!result.connected) {
        throw new Error("Database connection failed");
      }
      setCozeDb(url, true);
    } catch (e: any) {
      setCozeDb(url, false);
      setError(e?.response?.data?.detail || e?.message || "Database connection failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDbSubmit = async ({ url, workflowId }: { url: string; workflowId: string }) => {
    setLoading(true);
    setError(null);
    try {
      const result = await convertWorkflowFromDb({
        db_url: url,
        workflow_id: workflowId,
      });
      setCozeDb(url, true);
      setSourceMethod("database");
      setConversion(result.conversion_id, result.report);
      navigate(`/diff/${result.conversion_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Database fetch failed");
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
        {tab === "api" && <CozeApiConfig onSubmit={handleApiSubmit} />}
        {tab === "database" && (
          <DbConnectionConfig
            label="Coze"
            workflowLabel="Workflow ID"
            onTest={handleDbTest}
            onSubmit={handleDbSubmit}
            submitLabel="Import Workflow"
          />
        )}
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
