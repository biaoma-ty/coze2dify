import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PageShell from "../components/common/PageShell";
import FileUpload from "../components/upload/FileUpload";
import CozeApiConfig from "../components/upload/CozeApiConfig";
import DbConnectionConfig from "../components/upload/DbConnectionConfig";
import { useWorkflowStore } from "../store/workflowStore";
import { convertWorkflow, convertWorkflowFromApi, convertWorkflowFromDb } from "../api/conversion";
import { testDbConnection } from "../api/platform";
import { usePlatformStore } from "../store/platformStore";

type SourceTab = "file" | "api" | "database";

export default function MigratePage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<SourceTab>("file");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setConversion, setSourceMethod } = useWorkflowStore();
  const { setCozeCredentials, setCozeDb } = usePlatformStore();

  const tabs: { key: SourceTab; label: string; desc: string }[] = [
    { key: "file", label: t("migrate.tabs.file"), desc: t("migrate.tabs.fileDesc") },
    { key: "api", label: t("migrate.tabs.api"), desc: t("migrate.tabs.apiDesc") },
    { key: "database", label: t("migrate.tabs.database"), desc: t("migrate.tabs.databaseDesc") },
  ];

  const handleFileSelected = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const result = await convertWorkflow(file);
      setSourceMethod("upload");
      setConversion(result.conversion_id, result.report);
      navigate(`/migrate/diff/${result.conversion_id}`);
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
      navigate(`/migrate/diff/${result.conversion_id}`);
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
      navigate(`/migrate/diff/${result.conversion_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Database fetch failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.migrate") },
      ]}
      title={t("migrate.title")}
      subtitle={t("migrate.subtitle")}
    >
      {/* Tab Bar */}
      <div className="tab-bar" style={{ marginBottom: 24 }}>
        {tabs.map((tabItem) => (
          <button
            key={tabItem.key}
            className={`tab-btn ${tab === tabItem.key ? "tab-btn--active" : ""}`}
            onClick={() => setTab(tabItem.key)}
          >
            {tabItem.label}
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
            {t("migrate.processing")}
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>{t("common.error")}:</strong> {error}
        </div>
      )}
    </PageShell>
  );
}
