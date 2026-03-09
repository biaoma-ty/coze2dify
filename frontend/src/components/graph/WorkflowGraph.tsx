import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface Props {
  nodes: Node[];
  edges: Edge[];
  style?: React.CSSProperties;
}

export default function WorkflowGraph({ nodes, edges, style }: Props) {
  return (
    <div
      className="card"
      style={{
        height: 480,
        overflow: "hidden",
        background: "var(--c-surface-0)",
        ...style,
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--c-border-subtle)" gap={20} size={1} />
        <Controls
          style={{
            background: "var(--c-surface-2)",
            border: "1px solid var(--c-border)",
            borderRadius: 8,
          }}
        />
      </ReactFlow>
    </div>
  );
}
