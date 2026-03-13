import { COMPLEXITY_MAP, C, STATUS_MAP } from "../theme";
import type { ReviewItem, WorkflowSummary } from "../types";
import { summarizeWorkflows } from "../utils";
import Panel from "../components/Panel";
import ProgressBar from "../components/ProgressBar";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";
import WorkbenchButton from "../components/WorkbenchButton";
import { IcArrow } from "../components/icons";

interface OverviewViewProps {
  workflows: WorkflowSummary[];
  reviewQueue: ReviewItem[];
  onInspectWorkflow: (workflowId: string) => void;
}

export default function OverviewView({
  workflows,
  reviewQueue,
  onInspectWorkflow,
}: OverviewViewProps) {
  const summary = summarizeWorkflows(workflows, reviewQueue);
  const cards = [
    {
      label: "总工作流",
      value: summary.totalWorkflows,
      sub: `${summary.verifiedWorkflows} 已验证`,
      color: C.acc,
    },
    {
      label: "平均等价分",
      value: summary.averageScore.toFixed(1),
      sub: "目标≥95",
      color: summary.averageScore >= 95 ? C.ok : C.warn,
    },
    {
      label: "节点迁移率",
      value: `${((summary.migratedNodes / summary.totalNodes) * 100 || 0).toFixed(1)}%`,
      sub: `${summary.migratedNodes}/${summary.totalNodes}`,
      color: C.ok,
    },
    {
      label: "失败节点",
      value: summary.failedNodes,
      sub: "需人工",
      color: summary.failedNodes > 0 ? C.err : C.ok,
    },
    {
      label: "待审用例",
      value: summary.pendingReviews,
      sub: "人工审核",
      color: C.warn,
    },
  ];

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>迁移概览</h1>
      <p style={{ margin: "0 0 20px", color: C.tx2, fontSize: 12 }}>
        Coze → Dify 全局状态
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5,1fr)",
          gap: 10,
          marginBottom: 20,
        }}
      >
        {cards.map((card) => (
          <Panel key={card.label} style={{ padding: "14px 16px" }}>
            <div
              style={{
                fontSize: 10,
                color: C.tx3,
                textTransform: "uppercase",
                letterSpacing: ".05em",
                marginBottom: 6,
              }}
            >
              {card.label}
            </div>
            <div
              style={{
                fontSize: 24,
                fontWeight: 700,
                fontFamily: C.mono,
                color: card.color,
                lineHeight: 1,
              }}
            >
              {card.value}
            </div>
            <div style={{ fontSize: 10, color: C.tx3, marginTop: 4 }}>{card.sub}</div>
          </Panel>
        ))}
      </div>

      <Panel style={{ padding: "16px 18px", marginBottom: 20 }}>
        <SectionHeader>迁移进度</SectionHeader>
        {Object.entries(STATUS_MAP).map(([key, status]) => {
          const count = workflows.filter((workflow) => workflow.status === key).length;

          return (
            <div
              key={key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                marginBottom: 7,
              }}
            >
              <span
                style={{
                  width: 52,
                  fontSize: 11,
                  color: status.color,
                  fontWeight: 500,
                }}
              >
                {status.label}
              </span>
              <div style={{ flex: 1 }}>
                <ProgressBar value={count} total={workflows.length} tone={status.tone} />
              </div>
              <span
                style={{
                  width: 16,
                  fontSize: 10,
                  fontFamily: C.mono,
                  color: C.tx2,
                  textAlign: "right",
                }}
              >
                {count}
              </span>
            </div>
          );
        })}
      </Panel>

      <SectionHeader
        action={
          <WorkbenchButton compact variant="primary" type="button">
            <IcArrow />
            批量迁移
          </WorkbenchButton>
        }
      >
        工作流列表
      </SectionHeader>

      <Panel>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.bd}` }}>
              {["工作流", "状态", "节点", "等价分", "复杂度", ""].map((header) => (
                <th
                  key={header}
                  style={{
                    padding: "8px 12px",
                    fontSize: 10,
                    fontWeight: 700,
                    color: C.tx3,
                    textAlign: "left",
                    textTransform: "uppercase",
                  }}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {workflows.map((workflow) => {
              const status = STATUS_MAP[workflow.status];
              const complexity = COMPLEXITY_MAP[workflow.complexity];

              return (
                <tr
                  key={workflow.id}
                  onClick={() => onInspectWorkflow(workflow.id)}
                  style={{
                    borderBottom: `1px solid ${C.bd}`,
                    cursor: "pointer",
                  }}
                >
                  <td style={{ padding: "10px 12px" }}>
                    <div style={{ fontWeight: 600, fontSize: 12 }}>{workflow.name}</div>
                    <div style={{ fontSize: 10, color: C.tx3, fontFamily: C.mono }}>
                      {workflow.cozeId}
                    </div>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <ProgressBar
                        value={workflow.migrated}
                        total={workflow.nodes}
                        tone={workflow.failed > 0 ? "warning" : "success"}
                      />
                      <span style={{ fontSize: 10, fontFamily: C.mono, color: C.tx2 }}>
                        {workflow.migrated}/{workflow.nodes}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    {workflow.score > 0 ? (
                      <span
                        style={{
                          fontFamily: C.mono,
                          fontWeight: 700,
                          color:
                            workflow.score >= 90
                              ? C.ok
                              : workflow.score >= 70
                                ? C.warn
                                : C.err,
                        }}
                      >
                        {workflow.score.toFixed(1)}
                      </span>
                    ) : (
                      <span style={{ color: C.tx3 }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <StatusBadge tone={complexity.tone}>{complexity.label}</StatusBadge>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <WorkbenchButton compact variant="primary" type="button">
                      详情
                    </WorkbenchButton>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
