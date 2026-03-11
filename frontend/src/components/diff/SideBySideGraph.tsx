import { useState } from "react";
import { useTranslation } from "react-i18next";
import type {
  ConversionReport,
  NodeConversionResult,
  WorkflowGraphSummary,
  WorkflowGraphNodeSummary,
} from "../../types/ir";

interface SideBySideGraphProps {
  report: ConversionReport;
  sourceGraph: WorkflowGraphSummary | null;
  targetGraph: WorkflowGraphSummary | null;
  onNodeClick?: (result: NodeConversionResult) => void;
}

export default function SideBySideGraph({
  report,
  sourceGraph,
  targetGraph,
  onNodeClick,
}: SideBySideGraphProps) {
  const { t } = useTranslation();
  const [hoveredSourceId, setHoveredSourceId] = useState<string | null>(null);
  const [hoveredTargetId, setHoveredTargetId] = useState<string | null>(null);

  const sourceNodes = sourceGraph?.nodes || [];
  const targetNodes = targetGraph?.nodes || [];
  const resultIndex = Object.fromEntries(
    report.node_results.map((r) => [r.source_node_id, r])
  );
  const targetBySourceId = Object.fromEntries(
    report.node_results
      .filter((r) => r.target_node_id)
      .map((r) => [r.source_node_id, r.target_node_id!])
  );
  const sourceByTargetId = Object.fromEntries(
    report.node_results
      .filter((r) => r.target_node_id)
      .map((r) => [r.target_node_id!, r.source_node_id])
  );

  const highlightedTargetId = hoveredSourceId
    ? targetBySourceId[hoveredSourceId] || null
    : null;
  const highlightedSourceId = hoveredTargetId
    ? sourceByTargetId[hoveredTargetId] || null
    : null;

  return (
    <div className="side-by-side">
      {/* Source Panel */}
      <div className="side-by-side__panel">
        <div className="side-by-side__panel-header">{t("diff.cozeSource")}</div>
        {sourceNodes.length === 0 ? (
          <div style={{ color: "var(--c-text-tertiary)", fontSize: "0.82rem" }}>
            No source graph data
          </div>
        ) : (
          sourceNodes.map((node) => {
            const result = resultIndex[node.id];
            const status = result?.status || "skipped";
            const isHighlighted =
              highlightedSourceId === node.id || hoveredSourceId === node.id;
            return (
              <div
                key={node.id}
                className={`side-by-side__node side-by-side__node--${status} ${isHighlighted ? "side-by-side__node--highlight" : ""}`}
                onMouseEnter={() => setHoveredSourceId(node.id)}
                onMouseLeave={() => setHoveredSourceId(null)}
                onClick={() => result && onNodeClick?.(result)}
              >
                <div className="side-by-side__node-title">
                  {node.title || node.id}
                </div>
                <div className="side-by-side__node-meta">
                  {node.type} &middot; {node.id}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Divider */}
      <div className="side-by-side__divider" />

      {/* Target Panel */}
      <div className="side-by-side__panel">
        <div className="side-by-side__panel-header">{t("diff.difyTarget")}</div>
        {targetNodes.length === 0 ? (
          <div style={{ color: "var(--c-text-tertiary)", fontSize: "0.82rem" }}>
            No target graph data
          </div>
        ) : (
          targetNodes.map((node) => {
            const sourceId = sourceByTargetId[node.id];
            const result = sourceId ? resultIndex[sourceId] : undefined;
            const status = result?.status || "skipped";
            const isHighlighted =
              highlightedTargetId === node.id || hoveredTargetId === node.id;
            return (
              <div
                key={node.id}
                className={`side-by-side__node side-by-side__node--${status} ${isHighlighted ? "side-by-side__node--highlight" : ""}`}
                onMouseEnter={() => setHoveredTargetId(node.id)}
                onMouseLeave={() => setHoveredTargetId(null)}
                onClick={() => result && onNodeClick?.(result)}
              >
                <div className="side-by-side__node-title">
                  {node.title || node.id}
                </div>
                <div className="side-by-side__node-meta">
                  {node.type} &middot; {node.id}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
