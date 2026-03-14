import { useEffect, useState } from "react";
import { C } from "../theme";
import type { EquivalenceData, WorkflowSummary } from "../types";
import { getSeverityTone } from "../utils";
import Panel from "../components/Panel";
import SectionHeader from "../components/SectionHeader";
import SegmentTabs from "../components/SegmentTabs";
import StatusBadge from "../components/StatusBadge";
import { IcArrow, IcCheck, IcWarn, IcX } from "../components/icons";

type EquivalenceTab = "nodes" | "prompt" | "vars" | "plugins";

interface EquivalenceViewProps {
  workflow: WorkflowSummary;
  data: EquivalenceData;
}

export default function EquivalenceView({ workflow, data }: EquivalenceViewProps) {
  const [tab, setTab] = useState<EquivalenceTab>("nodes");
  const [selectedId, setSelectedId] = useState(data.nodes[0]?.id ?? "");
  const selectedNode = data.nodes.find((node) => node.id === selectedId) ?? data.nodes[0];

  useEffect(() => {
    setSelectedId(data.nodes[0]?.id ?? "");
  }, [data.nodes]);

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>等价验证</h1>
      <p style={{ margin: "0 0 14px", color: C.tx2, fontSize: 12 }}>{workflow.name}</p>

      <SegmentTabs
        activeKey={tab}
        items={[
          { key: "nodes", label: "节点对比", icon: <span>🔀</span> },
          { key: "prompt", label: "Prompt Diff", icon: <span>📝</span> },
          { key: "vars", label: "变量映射", icon: <span>📦</span> },
          { key: "plugins", label: "插件矩阵", icon: <span>🔌</span> },
        ]}
        onChange={setTab}
      />

      <div style={{ marginTop: 12 }}>
        {tab === "nodes" && (
          <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: 12 }}>
            <Panel style={{ padding: 6 }}>
              {data.nodes.map((node) => {
                const color =
                  node.status === "equivalent"
                    ? C.ok
                    : node.status === "warning"
                      ? C.warn
                      : C.err;

                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedId(node.id)}
                    style={{
                      padding: "8px 10px",
                      borderRadius: 4,
                      cursor: "pointer",
                      marginBottom: 1,
                      background: selectedNode?.id === node.id ? `${color}12` : "transparent",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: 14 }}>
                        {node.type === "llm"
                          ? "🧠"
                          : node.type === "knowledge"
                            ? "📚"
                            : node.type === "code"
                              ? "⚡"
                              : node.type === "http"
                                ? "🌐"
                                : node.type === "condition"
                                  ? "🔀"
                                  : "📦"}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 12, fontWeight: 500 }}>{node.name}</div>
                      </div>
                      <span style={{ color }}>
                        {node.status === "equivalent" ? (
                          <IcCheck />
                        ) : node.status === "warning" ? (
                          <IcWarn />
                        ) : (
                          <IcX />
                        )}
                      </span>
                    </div>
                  </div>
                );
              })}
            </Panel>

            <Panel style={{ padding: "16px 18px" }}>
              {selectedNode ? (
                <div>
                  <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
                    {selectedNode.type === "llm"
                      ? "🧠"
                      : selectedNode.type === "knowledge"
                        ? "📚"
                        : selectedNode.type === "code"
                          ? "⚡"
                          : selectedNode.type === "http"
                            ? "🌐"
                            : selectedNode.type === "condition"
                              ? "🔀"
                              : "📦"}{" "}
                    {selectedNode.name}
                  </div>

                  {selectedNode.diff.map((diff) => (
                    <div
                      key={diff.field}
                      style={{
                        padding: "6px 10px",
                        borderRadius: 5,
                        marginBottom: 8,
                        fontSize: 11,
                        background: diff.sev === "high" ? C.errD : C.warnD,
                      }}
                    >
                      <StatusBadge tone={getSeverityTone(diff.sev)}>
                        {diff.sev.toUpperCase()}
                      </StatusBadge>{" "}
                      {diff.field}: <span style={{ color: C.err }}>- {diff.coze}</span>{" "}
                      <span style={{ color: C.ok }}>+ {diff.dify}</span>
                    </div>
                  ))}

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 10,
                    }}
                  >
                    {[
                      { label: "Coze", cfg: selectedNode.cCfg, color: C.coze },
                      { label: "Dify", cfg: selectedNode.dCfg, color: C.dify },
                    ].map((side) => (
                      <div key={side.label}>
                        <div
                          style={{
                            fontSize: 10,
                            fontWeight: 700,
                            color: side.color,
                            marginBottom: 5,
                            textTransform: "uppercase",
                          }}
                        >
                          {side.label}
                        </div>
                        <pre
                          style={{
                            padding: 12,
                            borderRadius: 6,
                            background: "rgba(0,0,0,0.3)",
                            fontSize: 11,
                            fontFamily: C.mono,
                            lineHeight: 1.6,
                            margin: 0,
                            color: `${side.color}cc`,
                          }}
                        >
                          {JSON.stringify(side.cfg, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    height: 200,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: C.tx3,
                  }}
                >
                  ← 选择节点
                </div>
              )}
            </Panel>
          </div>
        )}

        {tab === "prompt" && (
          <Panel style={{ padding: 0, overflow: "hidden" }}>
            <div
              style={{
                display: "flex",
                gap: 12,
                padding: "12px 16px",
                borderBottom: `1px solid ${C.bd}`,
              }}
            >
              <StatusBadge tone="warning">{data.prompt.flags.length} 变更</StatusBadge>
              <StatusBadge tone="success">
                相似度 {(data.promptSimilarity * 100).toFixed(0)}%
              </StatusBadge>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              {[
                { label: "Coze", lines: data.prompt.coze, color: C.coze },
                { label: "Dify", lines: data.prompt.dify, color: C.dify },
              ].map((side) => (
                <div
                  key={side.label}
                  style={{
                    borderRight: side.label === "Coze" ? `1px solid ${C.bd}` : "none",
                  }}
                >
                  <div
                    style={{
                      padding: "8px 14px",
                      background: C.s2,
                      borderBottom: `1px solid ${C.bd}`,
                      fontSize: 10,
                      fontWeight: 700,
                      color: side.color,
                      textTransform: "uppercase",
                    }}
                  >
                    {side.label} System Prompt
                  </div>
                  {side.lines.map((line) => (
                    <div
                      key={`${side.label}-${line.ln}`}
                      style={{
                        display: "flex",
                        fontSize: 11,
                        fontFamily: C.mono,
                        lineHeight: "22px",
                        background:
                          line.t === "removed"
                            ? "rgba(255,82,100,0.06)"
                            : line.t === "added"
                              ? "rgba(34,221,160,0.06)"
                              : "transparent",
                      }}
                    >
                      <span
                        style={{
                          width: 24,
                          textAlign: "right",
                          paddingRight: 6,
                          color: C.tx3,
                          opacity: 0.4,
                          fontSize: 9,
                          flexShrink: 0,
                        }}
                      >
                        {line.ln}
                      </span>
                      <span
                        style={{
                          color:
                            line.t === "removed"
                              ? C.err
                              : line.t === "added"
                                ? C.ok
                                : C.tx,
                        }}
                      >
                        {line.t === "removed" ? "- " : line.t === "added" ? "+ " : "  "}
                        {line.text || " "}
                      </span>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            <div style={{ padding: "14px 16px", borderTop: `1px solid ${C.bd}` }}>
              <SectionHeader>AI 标记的关键变更</SectionHeader>
              {data.prompt.flags.map((flag) => {
                const tone = getSeverityTone(flag.sev);
                const background =
                  tone === "danger" ? C.errD : tone === "warning" ? C.warnD : C.accD;

                return (
                  <div
                    key={flag.desc}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 5,
                      marginBottom: 5,
                      background,
                    }}
                  >
                    <StatusBadge tone={tone}>
                      {flag.sev === "high"
                        ? "高风险"
                        : flag.sev === "medium"
                          ? "中风险"
                          : "低风险"}
                    </StatusBadge>
                    <span style={{ fontSize: 12, marginLeft: 6 }}>{flag.desc}</span>
                    <div style={{ fontSize: 10, color: C.tx3, marginTop: 2 }}>
                      影响: {flag.impact}
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>
        )}

        {tab === "vars" && (
          <Panel style={{ padding: "16px 18px" }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
              <StatusBadge tone="success">
                已映射 {data.variables.filter((item) => item.status === "mapped").length}
              </StatusBadge>
              <StatusBadge tone="danger">
                未映射 {data.variables.filter((item) => item.status === "unmapped").length}
              </StatusBadge>
            </div>

            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.bd}` }}>
                  {["Coze", "", "Dify", "方式", "状态"].map((header) => (
                    <th
                      key={header}
                      style={{
                        padding: "7px 10px",
                        fontSize: 9,
                        fontWeight: 700,
                        color: C.tx3,
                        textAlign: "left",
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.variables.map((mapping, index) => (
                  <tr key={`${mapping.coze}-${index}`} style={{ borderBottom: `1px solid ${C.bd}` }}>
                    <td
                      style={{
                        padding: "8px 10px",
                        fontFamily: C.mono,
                        fontSize: 11,
                        color: C.coze,
                      }}
                    >
                      {mapping.coze}
                    </td>
                    <td style={{ padding: "8px 4px", color: C.tx3 }}>
                      <IcArrow />
                    </td>
                    <td
                      style={{
                        padding: "8px 10px",
                        fontFamily: C.mono,
                        fontSize: 11,
                        color: mapping.status === "mapped" ? C.dify : C.err,
                      }}
                    >
                      {mapping.dify}
                    </td>
                    <td style={{ padding: "8px 10px" }}>
                      <StatusBadge tone={mapping.auto ? "success" : "warning"}>
                        {mapping.auto ? "自动" : "手动"}
                      </StatusBadge>
                    </td>
                    <td style={{ padding: "8px 10px" }}>
                      {mapping.status === "mapped" ? (
                        <span style={{ color: C.ok }}>
                          <IcCheck />
                        </span>
                      ) : (
                        <StatusBadge tone="danger">未映射</StatusBadge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        )}

        {tab === "plugins" && (
          <Panel style={{ padding: "16px 18px" }}>
            <SectionHeader>Plugin → Tool 兼容矩阵</SectionHeader>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.bd}` }}>
                  {["Coze 插件", "Dify Tool", "兼容性"].map((header) => (
                    <th
                      key={header}
                      style={{
                        padding: "7px 10px",
                        fontSize: 9,
                        fontWeight: 700,
                        color: C.tx3,
                        textAlign: "left",
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.plugins.map((plugin, index) => {
                  const tone =
                    plugin.compat === "full"
                      ? "success"
                      : plugin.compat === "partial"
                        ? "warning"
                        : plugin.compat === "custom"
                          ? "accent"
                          : "danger";
                  const label =
                    plugin.compat === "full"
                      ? "完全"
                      : plugin.compat === "partial"
                        ? "部分"
                        : plugin.compat === "custom"
                          ? "自建"
                          : "不支持";

                  return (
                    <tr key={`${plugin.coze}-${index}`} style={{ borderBottom: `1px solid ${C.bd}` }}>
                      <td style={{ padding: "8px 10px", fontSize: 12 }}>{plugin.coze}</td>
                      <td
                        style={{
                          padding: "8px 10px",
                          fontSize: 11,
                          fontFamily: C.mono,
                          color: plugin.compat === "none" ? C.err : C.dify,
                        }}
                      >
                        {plugin.dify}
                      </td>
                      <td style={{ padding: "8px 10px" }}>
                        <StatusBadge tone={tone}>{label}</StatusBadge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        )}
      </div>
    </div>
  );
}
