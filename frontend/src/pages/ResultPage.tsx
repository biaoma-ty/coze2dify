import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AlertTriangle, Rocket, Loader2 } from "lucide-react";
import PageShell from "../components/common/PageShell";
import EmptyState from "../components/common/EmptyState";
import Skeleton from "../components/common/Skeleton";
import ConversionReportView from "../components/result/ConversionReport";
import DownloadButton from "../components/result/DownloadButton";
import DirectWriteButton from "../components/result/DirectWriteButton";
import WarningList from "../components/result/WarningList";
import { useWorkflowStore } from "../store/workflowStore";
import { getConversion } from "../api/conversion";

export default function ResultPage() {
  const { conversionId } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
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

  const breadcrumb = [
    { label: t("nav.dashboard"), to: "/" },
    { label: t("nav.migrate"), to: "/migrate" },
    { label: t("result.title") },
  ];

  if (loading && !activeReport) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("result.title")}>
        <Skeleton variant="card" />
      </PageShell>
    );
  }

  if ((!activeReport || !conversionId) && error) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("result.title")}>
        <EmptyState icon={AlertTriangle} text={error} />
      </PageShell>
    );
  }

  if (!activeReport || !conversionId) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("result.title")}>
        <EmptyState icon={Rocket} text={t("diff.noData")} />
      </PageShell>
    );
  }

  const blockedReason =
    activeReport.blocking_issues[0] || "This workflow is outside the strict supported subset.";
  const manualReviewReason =
    activeReport.manual_review_reasons[0] || "Manual review is required before write-to-Dify.";
  const exportDescription = !activeReport.supported
    ? "Blocked workflows do not emit Dify DSL. Resolve the listed nodes before exporting."
    : activeReport.requires_manual_review
      ? "DSL download is available, but direct write stays locked until manual review is confirmed."
      : t("result.exportOptionsDesc");

  return (
    <PageShell
      breadcrumb={breadcrumb}
      title={t("result.title")}
      subtitle={`${activeReport.workflow_name} — ${t("result.subtitle")}`}
    >
      <ConversionReportView report={activeReport} />

      {!activeReport.supported && (
        <div className="alert alert--error" style={{ marginTop: 24 }}>
          <strong>Blocked by strict supported subset.</strong>
          <div style={{ marginTop: 6 }}>{blockedReason}</div>
          <div style={{ marginTop: 6, fontSize: "0.78rem" }}>
            No Dify DSL was generated for this conversion, so export actions are disabled.
          </div>
        </div>
      )}

      {activeReport.supported && activeReport.requires_manual_review && (
        <div className="alert alert--warning" style={{ marginTop: 24 }}>
          <strong>Manual review required before direct write.</strong>
          <div style={{ marginTop: 6 }}>{manualReviewReason}</div>
          <div style={{ marginTop: 6, fontSize: "0.78rem" }}>
            Download remains available. Direct write unlocks only after explicit operator confirmation.
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>{t("common.error")}:</strong> {error}
        </div>
      )}

      {/* Export Actions */}
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
          <div className="section-title">{t("result.exportOptions")}</div>
          <p style={{ fontSize: "0.82rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
            {exportDescription}
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <DownloadButton
            conversionId={conversionId}
            disabled={!activeReport.supported}
            disabledReason={!activeReport.supported ? blockedReason : ""}
          />
          <DirectWriteButton conversionId={conversionId} report={activeReport} />
        </div>
      </div>

      <WarningList results={activeReport.node_results} />
    </PageShell>
  );
}
