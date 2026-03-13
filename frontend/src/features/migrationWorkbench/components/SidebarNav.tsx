import { C, WORKBENCH_NAV } from "../theme";
import type { WorkbenchPageKey, WorkflowSummary } from "../types";

interface SidebarNavProps {
  activePage: WorkbenchPageKey;
  onNavigate: (page: WorkbenchPageKey) => void;
  workflows: WorkflowSummary[];
  selectedWorkflowId: string;
  onWorkflowSelect: (workflowId: string) => void;
}

export default function SidebarNav({
  activePage,
  onNavigate,
  workflows,
  selectedWorkflowId,
  onWorkflowSelect,
}: SidebarNavProps) {
  const groups = Array.from(new Set(WORKBENCH_NAV.map((item) => item.group)));

  return (
    <div
      style={{
        width: 200,
        background: C.s1,
        borderRight: `1px solid ${C.bd}`,
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
      }}
    >
      <div style={{ padding: "14px 14px 16px", borderBottom: `1px solid ${C.bd}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 26,
              height: 26,
              borderRadius: 6,
              background: `linear-gradient(135deg,${C.acc},${C.dify})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 12,
              fontWeight: 800,
              color: "#fff",
            }}
          >
            M
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700 }}>MigrationQA</div>
            <div style={{ fontSize: 8, color: C.tx3, fontFamily: C.mono }}>
              v2.0 · Coze→Dify
            </div>
          </div>
        </div>
      </div>

      <nav style={{ padding: "8px 6px", flex: 1, overflow: "auto" }}>
        {groups.map((group) => (
          <div key={group} style={{ marginBottom: 6 }}>
            <div
              style={{
                padding: "3px 8px",
                fontSize: 9,
                fontWeight: 700,
                color: C.tx3,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              {group}
            </div>
            {WORKBENCH_NAV.filter((item) => item.group === group).map((item) => {
              const active = activePage === item.key;

              return (
                <button
                  key={item.key}
                  onClick={() => onNavigate(item.key)}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 9px",
                    marginBottom: 1,
                    borderRadius: 4,
                    border: "none",
                    background: active ? C.accD : "transparent",
                    color: active ? C.acc : C.tx2,
                    fontSize: 11,
                    fontWeight: active ? 600 : 400,
                    fontFamily: C.ft,
                    cursor: "pointer",
                    textAlign: "left",
                  }}
                  type="button"
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div style={{ padding: 8, borderTop: `1px solid ${C.bd}` }}>
        <div
          style={{
            fontSize: 8,
            fontWeight: 700,
            color: C.tx3,
            textTransform: "uppercase",
            padding: "0 5px 4px",
          }}
        >
          当前工作流
        </div>
        <select
          value={selectedWorkflowId}
          onChange={(event) => onWorkflowSelect(event.target.value)}
          style={{
            width: "100%",
            padding: "6px 8px",
            borderRadius: 4,
            background: C.s2,
            border: `1px solid ${C.bd}`,
            color: C.tx,
            fontSize: 10,
            fontFamily: C.ft,
            cursor: "pointer",
            outline: "none",
          }}
        >
          {workflows.map((workflow) => (
            <option key={workflow.id} value={workflow.id}>
              {workflow.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
