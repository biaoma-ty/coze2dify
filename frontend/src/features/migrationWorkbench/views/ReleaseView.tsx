import { useState } from "react";
import { C } from "../theme";
import { CANARY_STAGES, ROLLBACK_VERSIONS } from "../mockData";
import type { WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";
import WorkbenchButton from "../components/WorkbenchButton";

interface ReleaseViewProps {
  workflow: WorkflowSummary;
}

export default function ReleaseView({ workflow }: ReleaseViewProps) {
  const [traffic, setTraffic] = useState(20);
  const activeIndex = CANARY_STAGES.findIndex((stage) => stage.st === "active");

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>灰度发布</h1>
      <p style={{ margin: "0 0 18px", color: C.tx2, fontSize: 12 }}>
        {workflow.name} · 流量切换 / 回滚
      </p>

      <Panel style={{ padding: "18px 20px", marginBottom: 16 }}>
        <SectionHeader>发布阶段</SectionHeader>
        <div style={{ display: "flex", alignItems: "center" }}>
          {CANARY_STAGES.map((stage, index) => (
            <div
              key={stage.label}
              style={{ display: "contents" }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 10,
                    fontWeight: 700,
                    fontFamily: C.mono,
                    background:
                      stage.st === "done" ? C.ok : stage.st === "active" ? C.acc : C.bd,
                    color: stage.st !== "pending" ? "#fff" : C.tx3,
                  }}
                >
                  {stage.pct}%
                </div>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: stage.st === "active" ? 700 : 400,
                    color:
                      stage.st === "active"
                        ? C.acc
                        : stage.st === "done"
                          ? C.ok
                          : C.tx3,
                  }}
                >
                  {stage.label}
                </div>
              </div>
              {index < CANARY_STAGES.length - 1 && (
                <div
                  style={{
                    flex: 1,
                    height: 2,
                    background: index < activeIndex ? C.ok : C.bd,
                    margin: "0 4px",
                    marginBottom: 20,
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Panel style={{ padding: "16px 18px" }}>
          <SectionHeader>流量分配</SectionHeader>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <span style={{ fontSize: 11, color: C.coze, fontWeight: 600 }}>
              Coze {100 - traffic}%
            </span>
            <span style={{ fontSize: 11, color: C.dify, fontWeight: 600 }}>
              Dify {traffic}%
            </span>
          </div>
          <div
            style={{
              height: 16,
              background: C.bd,
              borderRadius: 8,
              overflow: "hidden",
              marginBottom: 6,
              display: "flex",
            }}
          >
            <div
              style={{
                width: `${100 - traffic}%`,
                background: C.coze,
                transition: "width .3s",
              }}
            />
            <div
              style={{
                width: `${traffic}%`,
                background: C.dify,
                transition: "width .3s",
              }}
            />
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={traffic}
            onChange={(event) => setTraffic(Number(event.target.value))}
            style={{ width: "100%", marginBottom: 8 }}
          />
          <div style={{ display: "flex", gap: 5 }}>
            {[5, 20, 50, 100].map((preset) => (
              <WorkbenchButton
                key={preset}
                compact
                type="button"
                variant={traffic === preset ? "primary" : "secondary"}
                onClick={() => setTraffic(preset)}
              >
                {preset}%
              </WorkbenchButton>
            ))}
            <WorkbenchButton
              compact
              type="button"
              variant="danger"
              style={{ marginLeft: "auto" }}
            >
              回滚
            </WorkbenchButton>
          </div>
        </Panel>

        <Panel style={{ padding: "16px 18px" }}>
          <SectionHeader>版本历史</SectionHeader>
          {ROLLBACK_VERSIONS.map((version, index) => (
            <div
              key={version.ver}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 0",
                borderBottom: index < ROLLBACK_VERSIONS.length - 1 ? `1px solid ${C.bd}` : "none",
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background:
                    version.st === "active"
                      ? C.ok
                      : version.st === "rollback"
                        ? C.warn
                        : C.tx3,
                }}
              />
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: 12, fontWeight: 600, fontFamily: C.mono }}>
                  {version.ver}
                </span>{" "}
                <StatusBadge
                  tone={
                    version.st === "active"
                      ? "success"
                      : version.st === "rollback"
                        ? "warning"
                        : "muted"
                  }
                >
                  {version.st === "active"
                    ? "当前"
                    : version.st === "rollback"
                      ? "可回滚"
                      : "归档"}
                </StatusBadge>
                <div style={{ fontSize: 9, color: C.tx3 }}>
                  {version.ts} · 等价分:{" "}
                  <span
                    style={{
                      color: version.score >= 90 ? C.ok : C.warn,
                      fontFamily: C.mono,
                    }}
                  >
                    {version.score}
                  </span>
                </div>
              </div>
              {version.st === "rollback" && (
                <WorkbenchButton compact type="button" variant="danger">
                  回滚
                </WorkbenchButton>
              )}
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
