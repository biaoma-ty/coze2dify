import { C } from "../theme";
import { DAG_COZE, DAG_DIFY, STRUCTURE_DIFFS } from "../mockData";
import type { WorkflowSummary } from "../types";
import { getSeverityTone } from "../utils";
import DagGraph from "../components/DagGraph";
import Panel from "../components/Panel";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

interface TopologyViewProps {
  workflow: WorkflowSummary;
}

export default function TopologyView({ workflow }: TopologyViewProps) {
  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>DAG 拓扑对比</h1>
      <p style={{ margin: "0 0 18px", color: C.tx2, fontSize: 12 }}>
        {workflow.name} · 结构差异
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 12,
          marginBottom: 16,
        }}
      >
        {[
          { label: "Coze", graph: DAG_COZE, color: C.coze, platform: "coze" as const },
          { label: "Dify", graph: DAG_DIFY, color: C.dify, platform: "dify" as const },
        ].map((side) => (
          <Panel key={side.label} style={{ padding: "12px 14px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                marginBottom: 8,
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: 3,
                  background: side.color,
                }}
              />
              <span style={{ fontSize: 11, fontWeight: 600, color: side.color }}>
                {side.label}
              </span>
              <span
                style={{
                  fontSize: 10,
                  color: C.tx3,
                  fontFamily: C.mono,
                  marginLeft: "auto",
                }}
              >
                {side.graph.nodes.length}节点 · {side.graph.edges.length}连线
              </span>
            </div>
            <div
              style={{
                height: 200,
                background: C.bg,
                borderRadius: 5,
                border: `1px solid ${C.bd}`,
                padding: 6,
              }}
            >
              <DagGraph graph={side.graph} platform={side.platform} />
            </div>
          </Panel>
        ))}
      </div>

      <Panel style={{ padding: "14px 16px" }}>
        <SectionHeader>结构差异</SectionHeader>
        {STRUCTURE_DIFFS.map((item) => {
          const tone = getSeverityTone(item.sev);
          const color = tone === "danger" ? C.err : tone === "warning" ? C.warn : C.acc;
          const background = tone === "danger" ? C.errD : tone === "warning" ? C.warnD : C.accD;

          return (
            <div
              key={item.text}
              style={{
                padding: "8px 12px",
                borderRadius: 5,
                marginBottom: 5,
                fontSize: 12,
                background,
                border: `1px solid ${color}20`,
              }}
            >
              <StatusBadge tone={tone}>
                {item.sev === "high" ? "HIGH" : item.sev === "medium" ? "MED" : "LOW"}
              </StatusBadge>
              <span style={{ marginLeft: 6 }}>{item.text}</span>
            </div>
          );
        })}
      </Panel>
    </div>
  );
}
