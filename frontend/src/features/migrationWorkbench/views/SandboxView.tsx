import { useEffect, useRef, useState } from "react";
import { C } from "../theme";
import { SANDBOX_METRICS } from "../mockData";
import type { SandboxMessage, SandboxStatus, WorkflowSummary } from "../types";
import { buildSandboxReply, createMessageId } from "../utils";
import Panel from "../components/Panel";
import WorkbenchButton from "../components/WorkbenchButton";

interface SandboxViewProps {
  workflow: WorkflowSummary;
}

export default function SandboxView({ workflow }: SandboxViewProps) {
  const [status, setStatus] = useState<SandboxStatus>("idle");
  const [messages, setMessages] = useState<SandboxMessage[]>([]);
  const [input, setInput] = useState("");
  const timersRef = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    };
  }, []);

  const start = () => {
    setStatus("starting");
    timersRef.current.push(window.setTimeout(() => setStatus("running"), 1500));
  };

  const stop = () => {
    timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    timersRef.current = [];
    setStatus("idle");
    setMessages([]);
  };

  const send = () => {
    const text = input.trim();
    if (!text || status !== "running") {
      return;
    }

    setInput("");
    setMessages((current) => [...current, { id: createMessageId("user"), role: "user", text }]);

    timersRef.current.push(
      window.setTimeout(() => {
        const reply = buildSandboxReply(text, "coze");
        setMessages((current) => [
          ...current,
          {
            id: createMessageId("coze"),
            role: "coze",
            text: reply.text,
            latencyMs: reply.latencyMs,
          },
        ]);
      }, 800),
    );

    timersRef.current.push(
      window.setTimeout(() => {
        const reply = buildSandboxReply(text, "dify");
        setMessages((current) => [
          ...current,
          {
            id: createMessageId("dify"),
            role: "dify",
            text: reply.text,
            latencyMs: reply.latencyMs,
          },
        ]);
      }, 1200),
    );
  };

  const roleColors = {
    user: C.acc,
    coze: C.coze,
    dify: C.dify,
  } as const;

  const roleLabels = {
    user: "👤 输入",
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
              color: status === "running" ? C.ok : C.tx3,
            }}
          >
            <span
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                background: status === "running" ? C.ok : C.tx3,
              }}
            />
            {status === "idle" ? "未启动" : status === "starting" ? "启动中…" : "运行中"}
          </div>
          <WorkbenchButton
            type="button"
            variant={status === "idle" ? "success" : "danger"}
            onClick={status === "idle" ? start : stop}
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
              disabled={status !== "running"}
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
            <WorkbenchButton variant="primary" type="button" onClick={send}>
              发送
            </WorkbenchButton>
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
          {SANDBOX_METRICS.map((metric, index) => (
            <div
              key={metric.label}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
                borderBottom: index < SANDBOX_METRICS.length - 1 ? `1px solid ${C.bd}` : "none",
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
