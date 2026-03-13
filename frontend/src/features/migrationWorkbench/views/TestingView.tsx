import { useState } from "react";
import { C } from "../theme";
import type { TestingData, WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import SegmentTabs from "../components/SegmentTabs";
import StatusBadge from "../components/StatusBadge";
import WorkbenchButton from "../components/WorkbenchButton";
import { IcCheck, IcX } from "../components/icons";

type TestingTab = "cases" | "patterns";

interface TestingViewProps {
  workflow: WorkflowSummary;
  data: TestingData;
  onGenerate: () => void;
  onRunAll: () => void;
  generating: boolean;
  running: boolean;
}

export default function TestingView({
  workflow,
  data,
  onGenerate,
  onRunAll,
  generating,
  running,
}: TestingViewProps) {
  const [tab, setTab] = useState<TestingTab>("cases");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const summaryCards = [
    { label: "总用例", value: data.cases.length, color: C.acc },
    { label: "通过", value: data.cases.filter((item) => item.status === "pass").length, color: C.ok },
    { label: "失败", value: data.cases.filter((item) => item.status === "fail").length, color: C.err },
    { label: "错误模式", value: data.patterns.length, color: C.err },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>自动化测试</h1>
          <p style={{ margin: 0, color: C.tx2, fontSize: 12 }}>{workflow.name}</p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <WorkbenchButton variant="primary" type="button" onClick={onGenerate} disabled={generating}>
            {generating ? "生成中…" : "AI 生成"}
          </WorkbenchButton>
          <WorkbenchButton variant="success" type="button" onClick={onRunAll} disabled={running}>
            {running ? "运行中…" : "全部运行"}
          </WorkbenchButton>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: 8,
          marginBottom: 14,
        }}
      >
        {summaryCards.map((card) => (
          <Panel
            key={card.label}
            style={{
              padding: "10px 14px",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                fontSize: 18,
                fontWeight: 700,
                fontFamily: C.mono,
                color: card.color,
              }}
            >
              {card.value}
            </span>
            <span style={{ fontSize: 10, color: C.tx2 }}>{card.label}</span>
          </Panel>
        ))}
      </div>

      <SegmentTabs
        activeKey={tab}
        items={[
          { key: "cases", label: "用例", icon: <span>🧪</span> },
          { key: "patterns", label: "错误模式", icon: <span>🔍</span> },
        ]}
        onChange={setTab}
      />

      <div style={{ marginTop: 12 }}>
        {tab === "cases" && (
          <Panel>
            {data.cases.map((test, index) => {
              const expanded = expandedId === test.id;
              const similarityColor =
                test.sim >= 0.85 ? C.ok : test.sim >= 0.5 ? C.warn : C.err;
              const errorPattern = data.patterns.find((pattern) => pattern.key === test.ep);

              return (
                <div
                  key={test.id}
                  style={{
                    borderBottom: index < data.cases.length - 1 ? `1px solid ${C.bd}` : "none",
                  }}
                >
                  <div
                    onClick={() => setExpandedId(expanded ? null : test.id)}
                    style={{
                      padding: "10px 14px",
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      cursor: "pointer",
                    }}
                  >
                    <span
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: 4,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: test.status === "pass" ? C.okD : C.errD,
                        color: test.status === "pass" ? C.ok : C.err,
                      }}
                    >
                      {test.status === "pass" ? <IcCheck /> : <IcX />}
                    </span>
                    <div style={{ flex: 1, fontSize: 12, fontWeight: 500 }}>{test.name}</div>
                    <span
                      style={{
                        fontSize: 11,
                        fontFamily: C.mono,
                        fontWeight: 700,
                        color: similarityColor,
                      }}
                    >
                      {(test.sim * 100).toFixed(0)}%
                    </span>
                    <span style={{ fontSize: 10, fontFamily: C.mono, color: C.tx3 }}>
                      {test.dL > 0 ? `${test.dL}ms` : "ERR"}
                    </span>
                    {errorPattern && <StatusBadge tone="danger">{errorPattern.name}</StatusBadge>}
                    <span
                      style={{
                        color: C.tx3,
                        transform: expanded ? "rotate(180deg)" : "none",
                        transition: "transform .2s",
                        display: "inline-block",
                      }}
                    >
                      ▾
                    </span>
                  </div>

                  {expanded && (
                    <div
                      style={{
                        padding: "0 14px 14px",
                        borderTop: `1px dashed ${C.bd}`,
                        paddingTop: 10,
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr 1fr",
                        gap: 8,
                      }}
                    >
                      {[
                        { label: "输入", color: C.acc, value: test.input || "(空)" },
                        { label: "Coze", color: C.coze, value: test.cOut },
                        { label: "Dify", color: C.dify, value: test.dOut },
                      ].map((column) => (
                        <div key={column.label}>
                          <div
                            style={{
                              fontSize: 9,
                              fontWeight: 700,
                              color: column.color,
                              marginBottom: 4,
                              textTransform: "uppercase",
                            }}
                          >
                            {column.label}
                          </div>
                          <div
                            style={{
                              padding: 8,
                              borderRadius: 4,
                              background: C.bg,
                              border: `1px solid ${C.bd}`,
                              fontSize: 11,
                              fontFamily: C.mono,
                              minHeight: 40,
                              color: column.value.includes("ERROR") ? C.err : C.tx,
                            }}
                          >
                            {column.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </Panel>
        )}

        {tab === "patterns" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {data.patterns.map((pattern) => (
              <Panel key={pattern.id} style={{ padding: "14px 16px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    marginBottom: 8,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 7,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 14,
                      fontWeight: 700,
                      fontFamily: C.mono,
                      background: pattern.sev === "critical" ? C.errD : C.warnD,
                      color: pattern.sev === "critical" ? C.err : C.warn,
                    }}
                  >
                    {pattern.count}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {pattern.name}{" "}
                      <StatusBadge tone={pattern.sev === "critical" ? "danger" : "warning"}>
                        {pattern.sev === "critical" ? "严重" : "高"}
                      </StatusBadge>
                    </div>
                    <div style={{ fontSize: 11, color: C.tx2 }}>{pattern.desc}</div>
                  </div>
                </div>
                <div
                  style={{
                    padding: "8px 10px",
                    borderRadius: 4,
                    background: C.bg,
                    border: `1px solid ${C.bd}`,
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      color: C.ok,
                      marginBottom: 2,
                      textTransform: "uppercase",
                    }}
                  >
                    修复建议
                  </div>
                  <div style={{ fontSize: 11 }}>{pattern.fix}</div>
                </div>
              </Panel>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
