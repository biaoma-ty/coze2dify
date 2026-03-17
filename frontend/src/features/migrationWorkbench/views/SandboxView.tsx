import { useState } from "react";
import { C } from "../theme";
import type { SandboxData, WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import WorkbenchButton from "../components/WorkbenchButton";

interface SandboxViewProps {
  workflow: WorkflowSummary;
  data: SandboxData;
  onStart: () => void;
  onStop: () => void;
  onSend: (text: string) => void;
  sending: boolean;
}

export default function SandboxView({
  workflow,
  data,
  onStart,
  onStop,
  onSend,
  sending,
}: SandboxViewProps) {
  const [input, setInput] = useState("");
  const status = data.status;
  const messages = data.messages;

  const send = () => {
    const text = input.trim();
    if (!text || status !== "running") {
      return;
    }
    setInput("");
    onSend(text);
  };

  const roleColors = {
    user: C.acc,
    assistant: C.warn,
    coze: C.coze,
    dify: C.dify,
  } as const;

  const roleLabels = {
    user: "👤 输入",
    assistant: "🛠 工具",
    coze: "🔵 Coze",
    dify: "🟣 Dify",
  } as const;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>沙箱环境</h1>
          <p style={{ margin: 0, color: C.tx2, fontSize: 12 }}>{workflow.name}</p>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "3px 9px",
              borderRadius: 12,
              fontSize: 10,
              fontWeight: 600,
              background: status === "running" ? C.okD : `${C.tx3}15`,
              color: status === "running" ? C.ok : status === "starting" ? C.acc : C.tx3,
            }}
          >
            <span
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                background: status === "running" ? C.ok : status === "starting" ? C.acc : C.tx3,
              }}
            />
            {status === "idle" ? "未启动" : status === "starting" ? "启动中…" : "运行中"}
          </div>
          <WorkbenchButton
            type="button"
            variant={status === "idle" ? "success" : "danger"}
            onClick={status === "idle" ? onStart : onStop}
          >
            {status === "idle" ? "启动" : "停止"}
          </WorkbenchButton>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 260px",
          gap: 12,
          height: 420,
        }}
      >
        <Panel style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ flex: 1, overflow: "auto", padding: 12 }}>
            {status !== "running" && messages.length === 0 ? (
              <div
                style={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  color: C.tx3,
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.4 }}>🏖️</div>
                <div style={{ fontSize: 12 }}>启动沙箱后对比</div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: 6,
                    padding: "8px 10px",
                    borderRadius: 5,
                    background: `${roleColors[message.role]}10`,
                    borderLeft: `3px solid ${roleColors[message.role]}`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: 2,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 700,
                        color: roleColors[message.role],
                      }}
                    >
                      {roleLabels[message.role]}
                    </span>
                    {message.latencyMs && (
                      <span style={{ fontSize: 8, color: C.tx3 }}>{message.latencyMs}ms</span>
                    )}
                  </div>
                  <div style={{ fontSize: 12 }}>{message.text}</div>
                </div>
              ))
            )}
          </div>

          <div
            style={{
              display: "flex",
              gap: 5,
              padding: "8px 12px",
              borderTop: `1px solid ${C.bd}`,
            }}
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  send();
                }
              }}
              placeholder={status === "running" ? "输入消息…" : "先启动"}
              disabled={status !== "running" || sending}
              style={{
                flex: 1,
                padding: "7px 10px",
                borderRadius: 5,
                background: C.bg,
                border: `1px solid ${C.bd}`,
                color: C.tx,
                fontSize: 12,
                fontFamily: C.ft,
                outline: "none",
              }}
            />
            <WorkbenchButton variant="primary" type="button" onClick={send} disabled={sending}>
              {sending ? "发送中…" : "发送"}
            </WorkbenchButton>
          </div>
          <div
            style={{
              padding: "0 12px 10px",
              fontSize: 10,
              color: C.tx3,
            }}
          >
            试试：迁移当前工作流 / 批量迁移 / 生成测试 / 运行测试 / 查看状态
          </div>
        </Panel>

        <Panel style={{ padding: "12px 14px" }}>
          <div
            style={{
              fontSize: 9,
              fontWeight: 700,
              color: C.tx3,
              marginBottom: 8,
              textTransform: "uppercase",
            }}
          >
            实时指标
          </div>
          {data.metrics.map((metric, index) => (
            <div
              key={metric.label}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
                borderBottom: index < data.metrics.length - 1 ? `1px solid ${C.bd}` : "none",
              }}
            >
              <span style={{ fontSize: 10, color: C.tx3 }}>{metric.label}</span>
              <div
                style={{
                  display: "flex",
                  gap: 6,
                  fontFamily: C.mono,
                  fontSize: 10,
                }}
              >
                <span style={{ color: C.coze }}>{metric.coze}</span>
                <span style={{ color: C.tx3 }}>vs</span>
                <span style={{ color: C.dify }}>{metric.dify}</span>
              </div>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
