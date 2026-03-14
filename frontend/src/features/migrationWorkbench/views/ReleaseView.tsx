import { C } from "../theme";
import type { ReleaseData, WorkflowSummary } from "../types";
import Panel from "../components/Panel";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";
import WorkbenchButton from "../components/WorkbenchButton";

interface ReleaseViewProps {
  workflow: WorkflowSummary;
  data: ReleaseData;
  onTrafficChange: (traffic: number) => void;
  onRollback: (version?: string) => void;
  updating: boolean;
}

export default function ReleaseView({
  workflow,
  data,
  onTrafficChange,
  onRollback,
  updating,
}: ReleaseViewProps) {
  const activeIndex = data.stages.findIndex((stage) => stage.st === "active");

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>灰度发布</h1>
      <p style={{ margin: "0 0 18px", color: C.tx2, fontSize: 12 }}>
        {workflow.name} · 流量切换 / 回滚
      </p>

      <Panel style={{ padding: "18px 20px", marginBottom: 16 }}>
        <SectionHeader>发布阶段</SectionHeader>
        <div style={{ display: "flex", alignItems: "center" }}>
          {data.stages.map((stage, index) => (
            <div key={stage.label} style={{ display: "contents" }}>
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
                    background: stage.st === "done" ? C.ok : stage.st === "active" ? C.acc : C.bd,
                    color: stage.st !== "pending" ? "#fff" : C.tx3,
                  }}
                >
                  {stage.pct}%
                </div>
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: stage.st === "active" ? 700 : 400,
                    color: stage.st === "active" ? C.acc : stage.st === "done" ? C.ok : C.tx3,
                  }}
                >
                  {stage.label}
                </div>
              </div>
              {index < data.stages.length - 1 && (
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
              Coze {100 - data.traffic}%
            </span>
            <span style={{ fontSize: 11, color: C.dify, fontWeight: 600 }}>
              Dify {data.traffic}%
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
                width: `${100 - data.traffic}%`,
                background: C.coze,
                transition: "width .3s",
              }}
            />
            <div
              style={{
                width: `${data.traffic}%`,
                background: C.dify,
                transition: "width .3s",
              }}
            />
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={data.traffic}
            onChange={(event) => onTrafficChange(Number(event.target.value))}
            style={{ width: "100%", marginBottom: 8 }}
            disabled={updating}
          />
          <div style={{ display: "flex", gap: 5 }}>
            {[5, 20, 50, 100].map((preset) => (
              <WorkbenchButton
                key={preset}
                compact
                type="button"
                variant={data.traffic === preset ? "primary" : "secondary"}
                onClick={() => onTrafficChange(preset)}
                disabled={updating}
              >
                {preset}%
              </WorkbenchButton>
            ))}
            <WorkbenchButton
              compact
              type="button"
              variant="danger"
              style={{ marginLeft: "auto" }}
              onClick={() => onRollback()}
              disabled={updating}
            >
              回滚
            </WorkbenchButton>
          </div>
        </Panel>

        <Panel style={{ padding: "16px 18px" }}>
          <SectionHeader>版本历史</SectionHeader>
          {data.versions.map((version, index) => (
            <div
              key={version.ver}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "8px 0",
                borderBottom: index < data.versions.length - 1 ? `1px solid ${C.bd}` : "none",
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
                <WorkbenchButton
                  compact
                  type="button"
                  variant="danger"
                  onClick={() => onRollback(version.ver)}
                  disabled={updating}
                >
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
