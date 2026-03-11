import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Server, Globe, Info } from "lucide-react";
import PageShell from "../components/common/PageShell";
import { usePlatformStore } from "../store/platformStore";
import { connectCozeApi, connectDifyApi } from "../api/platform";

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const {
    cozeToken,
    cozeApiBase,
    cozeConnected,
    difyApiBase,
    difyApiKey,
    difyConnected,
    setCozeCredentials,
    setCozeConnected,
    setDifyCredentials,
    setDifyConnected,
  } = usePlatformStore();

  const [cozeTokenInput, setCozeTokenInput] = useState(cozeToken);
  const [cozeBaseInput, setCozeBaseInput] = useState(cozeApiBase);
  const [difyBaseInput, setDifyBaseInput] = useState(difyApiBase);
  const [difyKeyInput, setDifyKeyInput] = useState(difyApiKey);
  const [testing, setTesting] = useState<"coze" | "dify" | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [testSuccess, setTestSuccess] = useState<string | null>(null);

  const handleTestCoze = async () => {
    setTesting("coze");
    setTestError(null);
    setTestSuccess(null);
    try {
      const result = await connectCozeApi(cozeTokenInput, cozeBaseInput);
      setCozeCredentials(cozeTokenInput, cozeBaseInput);
      setCozeConnected(result.connected, result.workspaces);
      setTestSuccess("Coze API connected successfully");
    } catch (e: any) {
      setTestError(
        e?.response?.data?.detail || e?.message || "Coze API connection failed",
      );
    } finally {
      setTesting(null);
    }
  };

  const handleTestDify = async () => {
    setTesting("dify");
    setTestError(null);
    setTestSuccess(null);
    try {
      const result = await connectDifyApi(difyBaseInput, difyKeyInput);
      setDifyCredentials(difyBaseInput, difyKeyInput);
      setDifyConnected(result.connected);
      setTestSuccess("Dify API connected successfully");
    } catch (e: any) {
      setTestError(
        e?.response?.data?.detail || e?.message || "Dify API connection failed",
      );
    } finally {
      setTesting(null);
    }
  };

  const handleLanguageChange = (lang: string) => {
    void i18n.changeLanguage(lang);
    localStorage.setItem("c2d-lang", lang);
  };

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.settings") },
      ]}
      title={t("settings.title")}
      subtitle={t("settings.subtitle")}
    >
      {/* Alerts */}
      {testError && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {testError}
        </div>
      )}
      {testSuccess && (
        <div className="alert alert--success" style={{ marginBottom: 16 }}>
          {testSuccess}
        </div>
      )}

      {/* Platform Connections */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <Server size={20} />
          <span className="section-title" style={{ margin: 0 }}>
            {t("settings.platformConnections")}
          </span>
        </div>
        <p className="section-subtitle" style={{ marginBottom: 24 }}>
          {t("settings.platformConnectionsDesc")}
        </p>

        {/* Coze API */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", color: "var(--c-text-primary)" }}>
              {t("settings.cozeApi")}
            </h3>
            <span className={`badge ${cozeConnected ? "badge--mapped" : "badge--unmappable"}`}>
              {cozeConnected ? t("dashboard.health.connected") : t("dashboard.health.disconnected")}
            </span>
          </div>

          <div style={{ display: "grid", gap: 12, maxWidth: 600 }}>
            <div>
              <label style={{ display: "block", fontSize: "0.82rem", color: "var(--c-text-secondary)", marginBottom: 4 }}>
                Access Token
              </label>
              <input
                type="password"
                className="input"
                value={cozeTokenInput}
                onChange={(e) => setCozeTokenInput(e.target.value)}
                placeholder="pat_..."
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.82rem", color: "var(--c-text-secondary)", marginBottom: 4 }}>
                API Base URL
              </label>
              <input
                type="text"
                className="input"
                value={cozeBaseInput}
                onChange={(e) => setCozeBaseInput(e.target.value)}
                placeholder="https://api.coze.com"
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <button
                className="btn btn-primary"
                onClick={handleTestCoze}
                disabled={testing === "coze" || !cozeTokenInput}
              >
                {testing === "coze" ? t("common.testing") : t("sync.config.testConnections")}
              </button>
            </div>
          </div>
        </div>

        {/* Dify API */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", color: "var(--c-text-primary)" }}>
              {t("settings.difyApi")}
            </h3>
            <span className={`badge ${difyConnected ? "badge--mapped" : "badge--unmappable"}`}>
              {difyConnected ? t("dashboard.health.connected") : t("dashboard.health.disconnected")}
            </span>
          </div>

          <div style={{ display: "grid", gap: 12, maxWidth: 600 }}>
            <div>
              <label style={{ display: "block", fontSize: "0.82rem", color: "var(--c-text-secondary)", marginBottom: 4 }}>
                API Base URL
              </label>
              <input
                type="text"
                className="input"
                value={difyBaseInput}
                onChange={(e) => setDifyBaseInput(e.target.value)}
                placeholder="http://localhost/console/api"
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.82rem", color: "var(--c-text-secondary)", marginBottom: 4 }}>
                API Key
              </label>
              <input
                type="password"
                className="input"
                value={difyKeyInput}
                onChange={(e) => setDifyKeyInput(e.target.value)}
                placeholder="app-..."
                style={{ width: "100%" }}
              />
            </div>
            <div>
              <button
                className="btn btn-primary"
                onClick={handleTestDify}
                disabled={testing === "dify" || !difyBaseInput || !difyKeyInput}
              >
                {testing === "dify" ? t("common.testing") : t("sync.config.testConnections")}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* About / Language */}
      <div className="card" style={{ padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <Info size={20} />
          <span className="section-title" style={{ margin: 0 }}>
            {t("settings.about")}
          </span>
        </div>

        <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: "0.85rem", color: "var(--c-text-secondary)", minWidth: 80 }}>
              {t("settings.version")}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--c-text-primary)" }}>
              0.1.0
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Globe size={16} style={{ color: "var(--c-text-secondary)" }} />
            <span style={{ fontSize: "0.85rem", color: "var(--c-text-secondary)", minWidth: 64 }}>
              {t("settings.language")}
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className={`btn ${i18n.language === "en" ? "btn-primary" : "btn-ghost"}`}
                onClick={() => handleLanguageChange("en")}
                style={{ padding: "6px 14px", fontSize: "0.82rem" }}
              >
                {t("settings.english")}
              </button>
              <button
                className={`btn ${i18n.language === "zh" ? "btn-primary" : "btn-ghost"}`}
                onClick={() => handleLanguageChange("zh")}
                style={{ padding: "6px 14px", fontSize: "0.82rem" }}
              >
                {t("settings.chinese")}
              </button>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
