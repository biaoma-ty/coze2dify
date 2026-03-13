import { useEffect, useState } from "react";
import { useNavigate, useParams } from "@umijs/max";
import { useTranslation } from "react-i18next";
import { ArrowRight, RotateCcw, FileDown, Loader2, AlertTriangle, Eye } from "lucide-react";
import ConversionVisualBoard from "../components/diff/ConversionVisualBoard";
import SideBySideGraph from "../components/diff/SideBySideGraph";
import NodeDetailDrawer from "../components/diff/NodeDetailDrawer";
import HealthRing from "../components/diff/HealthRing";
import MappingTable from "../components/mapping/MappingTable";
import ConversionReportView from "../components/result/ConversionReport";
import PageShell from "../components/common/PageShell";
import EmptyState from "../components/common/EmptyState";
import Skeleton from "../components/common/Skeleton";
import { useWorkflowStore } from "../store/workflowStore";
import { getConversion } from "../api/conversion";
import type { NodeConversionResult } from "../types/ir";

export default function DiffPage() {
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
  const [selectedNode, setSelectedNode] = useState<NodeConversionResult | null>(null);
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
    { label: t("diff.title") },
  ];

  if (loading && !activeReport) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("diff.title")} subtitle={t("diff.subtitle")}>
        <div style={{ display: "grid", gap: 16 }}>
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>
      </PageShell>
    );
  }

  if (error && !activeReport) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("diff.title")} subtitle={t("diff.subtitle")}>
        <EmptyState icon={AlertTriangle} text={error} />
      </PageShell>
    );
  }

  if (!activeReport) {
    return (
      <PageShell breadcrumb={breadcrumb} title={t("diff.title")} subtitle={t("diff.subtitle")}>
        <EmptyState icon={Eye} text={t("diff.noData")} />
      </PageShell>
    );
  }

  const mapped = activeReport.mapped_count;
  const total = activeReport.total_nodes;
  const pct = total > 0 ? Math.round((mapped / total) * 100) : 0;

  return (
    <PageShell breadcrumb={breadcrumb} title={t("diff.title")} subtitle={t("diff.subtitle")}>
      {/* Summary Header */}
      <div
        className="card card--elevated"
        style={{
          padding: 20,
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "1.1rem", fontWeight: 700, fontFamily: "var(--font-display)" }}>
            {activeReport.workflow_name}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--c-text-tertiary)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
            #{conversionId}
          </div>
        </div>
        <HealthRing
          mapped={activeReport.mapped_count}
          partial={activeReport.partial_count}
          unmappable={activeReport.unmappable_count}
          skipped={activeReport.skipped_count}
          size={64}
          label={`${pct}%`}
        />
      </div>

      {/* Report Stat Cards */}
      <ConversionReportView report={activeReport} />

      {/* Side-by-Side Graph */}
      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 8 }}>{t("diff.sideBySide")}</div>
        <p className="section-subtitle" style={{ marginBottom: 16 }}>{t("diff.sideBySideDesc")}</p>
        <SideBySideGraph
          report={activeReport}
          sourceGraph={activeDetail?.source_graph || null}
          targetGraph={activeDetail?.target_graph || null}
          onNodeClick={setSelectedNode}
        />
      </div>

      {/* Visual Diff Board */}
      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 8 }}>{t("diff.visualDiff")}</div>
        <p className="section-subtitle" style={{ marginBottom: 16 }}>{t("diff.visualDiffDesc")}</p>
        <ConversionVisualBoard
          report={activeReport}
          sourceGraph={activeDetail?.source_graph || null}
          targetGraph={activeDetail?.target_graph || null}
        />
      </div>

      {/* Node Details Table */}
      <div style={{ marginTop: 24 }}>
        <div className="section-title" style={{ marginBottom: 16 }}>{t("diff.nodeDetails")}</div>
        <MappingTable results={activeReport.node_results} />
      </div>

      {error && (
        <div className="alert alert--error" style={{ marginTop: 20 }}>
          <strong>{t("common.error")}:</strong> {error}
        </div>
      )}

      {/* Action Bar */}
      <div style={{ marginTop: 32, display: "flex", gap: 12 }}>
        <button
          className="btn btn-primary"
          onClick={() => navigate(`/migrate/result/${conversionId}`)}
        >
          <ArrowRight size={15} />
          {t("diff.continueToExport")}
        </button>
        <button className="btn btn-secondary" onClick={() => {
          const report = activeReport;
          const lines = [
            `# Conversion Report: ${report.workflow_name}`,
            ``,
            `- Total Nodes: ${report.total_nodes}`,
            `- Mapped: ${report.mapped_count} (${total > 0 ? ((report.mapped_count / total) * 100).toFixed(1) : 0}%)`,
            `- Partial: ${report.partial_count} (${total > 0 ? ((report.partial_count / total) * 100).toFixed(1) : 0}%)`,
            `- Unmappable: ${report.unmappable_count} (${total > 0 ? ((report.unmappable_count / total) * 100).toFixed(1) : 0}%)`,
            `- Skipped: ${report.skipped_count}`,
            ``,
            `## Node Mappings`,
            ``,
            `| Source ID | Source Type | Status | Target ID | Target Type | Warnings |`,
            `|----------|------------|--------|-----------|------------|----------|`,
            ...report.node_results.map((r) =>
              `| ${r.source_node_id} | ${r.source_node_type} | ${r.status} | ${r.target_node_id || "-"} | ${r.target_node_type || "-"} | ${r.warnings.join("; ") || "-"} |`
            ),
            ``,
            ...(report.warnings.length > 0
              ? [`## Warnings`, ``, ...report.warnings.map((w) => `- ${w}`)]
              : []),
            ...(report.errors.length > 0
              ? [`## Errors`, ``, ...report.errors.map((e) => `- ${e}`)]
              : []),
          ];
          const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `conversion-report-${conversionId}.md`;
          a.click();
          URL.revokeObjectURL(url);
        }}>
          <FileDown size={15} />
          {t("diff.downloadReport")}
        </button>
        <button className="btn btn-ghost" onClick={() => navigate("/migrate")}>
          <RotateCcw size={15} />
          {t("diff.startOver")}
        </button>
      </div>

      {/* Node Detail Drawer */}
      <NodeDetailDrawer
        node={selectedNode}
        sourceGraph={activeDetail?.source_graph || null}
        targetGraph={activeDetail?.target_graph || null}
        onClose={() => setSelectedNode(null)}
      />
    </PageShell>
  );
}
