import type {
  ConversionReport,
  MappingStatus,
  NodeConversionResult,
  WorkflowGraphNodeSummary,
  WorkflowGraphSummary,
} from "../../types/ir";

const LANE_CONFIG: Array<{
  status: MappingStatus;
  label: string;
  tone: "green" | "amber" | "red" | "slate";
  description: string;
}> = [
  {
    status: "mapped",
    label: "Mapped",
    tone: "green",
    description: "Cleanly translated to Dify nodes with matching structure.",
  },
  {
    status: "partial",
    label: "Partial",
    tone: "amber",
    description: "Converted, but with warnings, gaps, or downgraded behavior.",
  },
  {
    status: "unmappable",
    label: "Unmappable",
    tone: "red",
    description: "No safe Dify equivalent was generated for this Coze node.",
  },
  {
    status: "skipped",
    label: "Skipped",
    tone: "slate",
    description: "Intentionally omitted from the output graph or inlined elsewhere.",
  },
];

export default function ConversionVisualBoard({
  report,
  sourceGraph,
  targetGraph,
}: {
  report: ConversionReport;
  sourceGraph: WorkflowGraphSummary | null;
  targetGraph: WorkflowGraphSummary | null;
}) {
  const sourceIndex = toNodeIndex(sourceGraph);
  const targetIndex = toNodeIndex(targetGraph);

  return (
    <div className="change-board">
      <div className="change-overview-grid">
        <GraphSummaryCard
          label="Coze Source"
          tone="accent"
          graph={sourceGraph}
          fallback="Source graph summary is not available for this conversion snapshot."
        />
        <GraphSummaryCard
          label="Dify Target"
          tone="blue"
          graph={targetGraph}
          fallback="Target graph summary is not available for this conversion snapshot."
        />
      </div>

      <div className="change-lane-grid" style={{ marginTop: 20 }}>
        {LANE_CONFIG.map((lane, index) => {
          const items = report.node_results.filter((result) => result.status === lane.status);
          return (
            <section key={lane.status} className={`card change-lane change-lane--${lane.tone} fade-in fade-in-${index + 1}`}>
              <div className="change-lane__header">
                <div>
                  <div className="change-lane__title">{lane.label}</div>
                  <p className="change-lane__description">{lane.description}</p>
                </div>
                <div className="change-lane__count">{items.length}</div>
              </div>

              <div className="change-lane__body">
                {items.length > 0 ? (
                  items.map((result) => (
                    <ConversionNodeCard
                      key={result.source_node_id}
                      result={result}
                      sourceNode={sourceIndex[result.source_node_id] || null}
                      targetNode={result.target_node_id ? targetIndex[result.target_node_id] || null : null}
                    />
                  ))
                ) : (
                  <div className="change-lane__empty">No {lane.label.toLowerCase()} nodes in this conversion.</div>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

function GraphSummaryCard({
  label,
  tone,
  graph,
  fallback,
}: {
  label: string;
  tone: "accent" | "blue";
  graph: WorkflowGraphSummary | null;
  fallback: string;
}) {
  if (!graph) {
    return (
      <div className={`card change-panel change-panel--${tone}`}>
        <div className="change-panel__label">{label}</div>
        <div className="change-panel__empty">{fallback}</div>
      </div>
    );
  }

  const nestedCount = graph.nodes.filter((node) => node.parent_id).length;
  const previewNodes = graph.nodes.slice(0, 6);

  return (
    <div className={`card change-panel change-panel--${tone}`}>
      <div className="change-panel__label">{label}</div>

      <div className="change-panel__metrics">
        <MetricPill label="Nodes" value={graph.node_count} />
        <MetricPill label="Edges" value={graph.edge_count} />
        <MetricPill label="Nested" value={nestedCount} />
      </div>

      <div className="change-panel__chips">
        {previewNodes.map((node) => (
          <div key={node.id} className="change-chip">
            <div className="change-chip__title">{node.title || node.id}</div>
            <div className="change-chip__meta">
              {node.type || "unknown"} • {node.id}
            </div>
          </div>
        ))}
        {graph.nodes.length > previewNodes.length ? (
          <div className="change-chip change-chip--more">+{graph.nodes.length - previewNodes.length} more</div>
        ) : null}
      </div>
    </div>
  );
}

function ConversionNodeCard({
  result,
  sourceNode,
  targetNode,
}: {
  result: NodeConversionResult;
  sourceNode: WorkflowGraphNodeSummary | null;
  targetNode: WorkflowGraphNodeSummary | null;
}) {
  const parentLabel = sourceNode?.parent_id ? `Nested in ${sourceNode.parent_id}` : null;

  return (
    <article className={`change-item change-item--${toneForMappingStatus(result.status)}`}>
      <div className="change-item__header">
        <div>
          <div className="change-item__title">{sourceNode?.title || result.source_node_id}</div>
          <div className="change-item__meta">
            {sourceNode?.type || result.source_node_type} • {result.source_node_id}
          </div>
        </div>
        <span className={`badge ${badgeClassForMappingStatus(result.status)}`}>{result.status}</span>
      </div>

      {parentLabel ? <div className="change-item__hint">{parentLabel}</div> : null}

      <div className="change-route">
        <div className="change-route__node">
          <div className="change-route__label">Coze</div>
          <div className="change-route__title">{sourceNode?.title || result.source_node_id}</div>
        </div>
        <div className="change-route__arrow">→</div>
        <div className="change-route__node">
          <div className="change-route__label">Dify</div>
          <div className="change-route__title">
            {targetNode?.title || result.target_node_id || "No target node emitted"}
          </div>
          <div className="change-route__meta">
            {targetNode?.type || result.target_node_type || "unmapped"}
          </div>
        </div>
      </div>

      {result.warnings.length > 0 ? (
        <div className="change-item__note change-item__note--warning">{result.warnings.join(" ")}</div>
      ) : null}
      {result.errors.length > 0 ? (
        <div className="change-item__note change-item__note--error">{result.errors.join(" ")}</div>
      ) : null}
    </article>
  );
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="change-metric">
      <div className="change-metric__value">{value}</div>
      <div className="change-metric__label">{label}</div>
    </div>
  );
}

function toNodeIndex(graph: WorkflowGraphSummary | null) {
  return Object.fromEntries((graph?.nodes || []).map((node) => [node.id, node]));
}

function toneForMappingStatus(status: MappingStatus) {
  switch (status) {
    case "mapped":
      return "green";
    case "partial":
      return "amber";
    case "unmappable":
      return "red";
    case "skipped":
    default:
      return "slate";
  }
}

function badgeClassForMappingStatus(status: MappingStatus) {
  switch (status) {
    case "mapped":
      return "badge--mapped";
    case "partial":
      return "badge--partial";
    case "unmappable":
      return "badge--unmappable";
    case "skipped":
    default:
      return "badge--skipped";
  }
}
