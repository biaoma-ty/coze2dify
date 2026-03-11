import { useTranslation } from "react-i18next";
import Drawer from "../common/Drawer";
import VerificationChecklist from "./VerificationChecklist";
import type { NodeConversionResult, WorkflowGraphSummary } from "../../types/ir";

interface NodeDetailDrawerProps {
  node: NodeConversionResult | null;
  sourceGraph: WorkflowGraphSummary | null;
  targetGraph: WorkflowGraphSummary | null;
  onClose: () => void;
}

export default function NodeDetailDrawer({
  node,
  sourceGraph,
  targetGraph,
  onClose,
}: NodeDetailDrawerProps) {
  const { t } = useTranslation();

  if (!node) {
    return null;
  }

  const sourceNodeInfo = sourceGraph?.nodes.find((n) => n.id === node.source_node_id);
  const targetNodeInfo = node.target_node_id
    ? targetGraph?.nodes.find((n) => n.id === node.target_node_id)
    : null;

  const badgeClass =
    node.status === "mapped"
      ? "badge--mapped"
      : node.status === "partial"
        ? "badge--partial"
        : node.status === "unmappable"
          ? "badge--unmappable"
          : "badge--skipped";

  return (
    <Drawer
      open={true}
      onClose={onClose}
      title={t("diff.nodeDrawer.title")}
      width={460}
    >
      {/* Source Node */}
      <div style={{ marginBottom: 20 }}>
        <div className="label">{t("diff.nodeDrawer.sourceNode")}</div>
        <div className="card" style={{ padding: 14 }}>
          <div style={{ fontWeight: 700, fontSize: "0.9rem" }}>
            {sourceNodeInfo?.title || node.source_node_id}
          </div>
          <div style={{ fontSize: "0.78rem", color: "var(--c-text-tertiary)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
            {node.source_node_type} &middot; {node.source_node_id}
          </div>
          {sourceNodeInfo?.parent_id && (
            <div style={{ fontSize: "0.75rem", color: "var(--c-text-tertiary)", marginTop: 4 }}>
              Nested in {sourceNodeInfo.parent_id}
            </div>
          )}
        </div>
      </div>

      {/* Target Node */}
      <div style={{ marginBottom: 20 }}>
        <div className="label">{t("diff.nodeDrawer.targetNode")}</div>
        <div className="card" style={{ padding: 14 }}>
          {node.target_node_id ? (
            <>
              <div style={{ fontWeight: 700, fontSize: "0.9rem" }}>
                {targetNodeInfo?.title || node.target_node_id}
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--c-text-tertiary)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
                {node.target_node_type || "unknown"} &middot; {node.target_node_id}
              </div>
            </>
          ) : (
            <div style={{ color: "var(--c-text-tertiary)", fontSize: "0.82rem" }}>
              No target node emitted
            </div>
          )}
        </div>
      </div>

      {/* Mapping Status */}
      <div style={{ marginBottom: 20 }}>
        <div className="label">{t("diff.nodeDrawer.mappingStatus")}</div>
        <span className={`badge ${badgeClass}`}>{node.status}</span>
      </div>

      {/* Verification Checklist */}
      <div style={{ marginBottom: 20 }}>
        <div className="label">{t("diff.nodeDrawer.verification")}</div>
        <VerificationChecklist result={node} />
      </div>

      {/* Warnings */}
      {node.warnings.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div className="label">{t("diff.nodeDrawer.warnings")}</div>
          {node.warnings.map((w, i) => (
            <div key={i} className="alert alert--warning" style={{ marginBottom: 8, fontSize: "0.82rem" }}>
              {w}
            </div>
          ))}
        </div>
      )}

      {/* Errors */}
      {node.errors.length > 0 && (
        <div>
          <div className="label">{t("diff.nodeDrawer.errors")}</div>
          {node.errors.map((e, i) => (
            <div key={i} className="alert alert--error" style={{ marginBottom: 8, fontSize: "0.82rem" }}>
              {e}
            </div>
          ))}
        </div>
      )}
    </Drawer>
  );
}
