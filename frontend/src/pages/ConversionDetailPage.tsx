import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Download, ExternalLink } from "lucide-react";
import PageShell from "../components/common/PageShell";
import Skeleton from "../components/common/Skeleton";
import ConversionReportView from "../components/result/ConversionReport";
import ConversionVisualBoard from "../components/diff/ConversionVisualBoard";
import MappingTable from "../components/mapping/MappingTable";
import { getConversion } from "../api/conversion";
import type { ConversionDetail } from "../types/ir";

export default function ConversionDetailPage() {
  const { t } = useTranslation();
  const { conversionId } = useParams<{ conversionId: string }>();
  const [detail, setDetail] = useState<ConversionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!conversionId) return;
    let cancelled = false;

    setLoading(true);
    setError(null);
    getConversion(conversionId)
      .then((result) => {
        if (!cancelled) {
          setDetail(result);
        }
      })
      .catch((e: any) => {
        if (!cancelled) {
          setError(
            e?.response?.data?.detail || e?.message || "Failed to load conversion detail",
          );
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
  }, [conversionId]);

  const report = detail?.report;

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.history"), to: "/history" },
        {
          label: detail
            ? detail.source_workflow_name || `Conversion ${conversionId?.slice(0, 8)}...`
            : t("common.loading"),
        },
      ]}
      title={
        detail
          ? detail.source_workflow_name || t("diff.title")
          : t("diff.title")
      }
      subtitle={
        detail
          ? `${t("diff.summaryHeader")} - ${detail.status}`
          : t("diff.subtitle")
      }
      actions={
        detail ? (
          <div style={{ display: "flex", gap: 8 }}>
            <Link
              to={`/migrate/diff/${conversionId}`}
              className="btn btn-secondary"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <ExternalLink size={14} />
              {t("diff.visualDiff")}
            </Link>
            <Link
              to={`/result/${conversionId}`}
              className="btn btn-primary"
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <Download size={14} />
              {t("result.exportOptions")}
            </Link>
          </div>
        ) : undefined
      }
    >
      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading && (
        <div style={{ display: "grid", gap: 16 }}>
          <Skeleton variant="card" count={1} />
          <Skeleton variant="row" count={6} />
        </div>
      )}

      {!loading && report && detail && (
        <>
          {/* Conversion Report */}
          <div style={{ marginBottom: 24 }}>
            <ConversionReportView report={report} />
          </div>

          {/* Write Result Info */}
          {detail.write_result && (
            <div
              className={`alert ${detail.write_result.status === "succeeded" ? "alert--success" : "alert--error"}`}
              style={{ marginBottom: 24 }}
            >
              <strong>
                {detail.write_result.status === "succeeded"
                  ? "Written to Dify"
                  : "Write Failed"}
              </strong>
              {detail.write_result.app_id && (
                <span style={{ marginLeft: 8 }}>
                  App ID: {detail.write_result.app_id}
                </span>
              )}
              {detail.write_result.error && (
                <span style={{ marginLeft: 8 }}>
                  {detail.write_result.error}
                </span>
              )}
            </div>
          )}

          {/* Visual Board */}
          <div style={{ marginBottom: 24 }}>
            <div className="section-title" style={{ marginBottom: 12 }}>
              {t("diff.visualDiff")}
            </div>
            <p className="section-subtitle" style={{ marginBottom: 16 }}>
              {t("diff.visualDiffDesc")}
            </p>
            <ConversionVisualBoard
              report={report}
              sourceGraph={detail.source_graph || null}
              targetGraph={detail.target_graph || null}
            />
          </div>

          {/* Mapping Table */}
          <div>
            <div className="section-title" style={{ marginBottom: 16 }}>
              {t("diff.nodeDetails")}
            </div>
            <MappingTable results={report.node_results} />
          </div>
        </>
      )}

      {!loading && !detail && !error && (
        <div className="empty-state card" style={{ borderStyle: "dashed" }}>
          <p className="empty-state__text">{t("diff.noData")}</p>
        </div>
      )}
    </PageShell>
  );
}
