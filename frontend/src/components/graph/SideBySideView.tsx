import type { Node, Edge } from "@xyflow/react";
import WorkflowGraph from "./WorkflowGraph";

interface Props {
  sourceNodes: Node[];
  sourceEdges: Edge[];
  targetNodes: Node[];
  targetEdges: Edge[];
}

export default function SideBySideView({ sourceNodes, sourceEdges, targetNodes, targetEdges }: Props) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 12,
        }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: 3,
            background: "var(--c-blue)",
          }} />
          <span className="label" style={{ marginBottom: 0 }}>Coze · Source</span>
        </div>
        <WorkflowGraph nodes={sourceNodes} edges={sourceEdges} />
      </div>
      <div>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 12,
        }}>
          <div style={{
            width: 10,
            height: 10,
            borderRadius: 3,
            background: "var(--c-accent)",
          }} />
          <span className="label" style={{ marginBottom: 0 }}>Dify · Target</span>
        </div>
        <WorkflowGraph nodes={targetNodes} edges={targetEdges} />
      </div>
    </div>
  );
}
