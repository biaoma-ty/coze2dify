import { C } from "../theme";
import type { KnowledgeBaseRecord, WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import { IcCheck } from "../components/icons";
import StatusBadge from "../components/StatusBadge";

interface KnowledgeViewProps {
  workflow: WorkflowSummary;
  records: KnowledgeBaseRecord[];
}

export default function KnowledgeView({ workflow, records }: KnowledgeViewProps) {
  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>知识库迁移</h1>
      <p style={{ margin: "0 0 18px", color: C.tx2, fontSize: 12 }}>
        {workflow.name} · 分片 / 召回一致性
      </p>

      <Panel style={{ padding: "16px 18px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.bd}` }}>
              {["知识库", "Coze分片", "Dify分片", "召回率", "Embedding", "状态"].map((header) => (
                <th
                  key={header}
                  style={{
                    padding: "7px 10px",
                    fontSize: 9,
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
            {records.map((record, index) => (
              <tr key={`${record.name}-${index}`} style={{ borderBottom: `1px solid ${C.bd}` }}>
                <td style={{ padding: "8px 10px", fontWeight: 500, fontSize: 12 }}>
                  {record.name}
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    fontFamily: C.mono,
                    fontSize: 11,
                    color: C.coze,
                  }}
                >
                  {record.cC}
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    fontFamily: C.mono,
                    fontSize: 11,
                    color: C.dify,
                  }}
                >
                  {record.dC}
                </td>
                <td style={{ padding: "8px 10px" }}>
                  <span
                    style={{
                      fontFamily: C.mono,
                      fontWeight: 700,
                      color:
                        record.match >= 0.9 ? C.ok : record.match >= 0.8 ? C.warn : C.err,
                    }}
                  >
                    {(record.match * 100).toFixed(0)}%
                  </span>
                </td>
                <td
                  style={{
                    padding: "8px 10px",
                    fontSize: 10,
                    color: record.emb === "不一致" ? C.err : C.tx2,
                  }}
                >
                  {record.emb}
                </td>
                <td style={{ padding: "8px 10px" }}>
                  {record.ok ? (
                    <span style={{ color: C.ok }}>
                      <IcCheck />
                    </span>
                  ) : (
                    <StatusBadge tone="danger">异常</StatusBadge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
