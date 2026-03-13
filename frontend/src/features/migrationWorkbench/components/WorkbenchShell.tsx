import type { ReactNode } from "react";
import { C, STATUS_MAP } from "../theme";
import type { WorkbenchPageKey, WorkflowSummary } from "../types";
import SidebarNav from "./SidebarNav";
import StatusBadge from "./StatusBadge";

interface WorkbenchShellProps {
  activePage: WorkbenchPageKey;
  onNavigate: (page: WorkbenchPageKey) => void;
  workflows: WorkflowSummary[];
  selectedWorkflow: WorkflowSummary;
  onWorkflowSelect: (workflowId: string) => void;
  children: ReactNode;
}

export default function WorkbenchShell({
  activePage,
  onNavigate,
  workflows,
  selectedWorkflow,
  onWorkflowSelect,
  children,
}: WorkbenchShellProps) {
  const statusMeta = STATUS_MAP[selectedWorkflow.status];

  return (
    <div
      style={{
        fontFamily: C.ft,
        background: C.bg,
        color: C.tx,
        minHeight: "100vh",
        display: "flex",
        fontSize: 13,
        lineHeight: 1.5,
      }}
    >
      <SidebarNav
        activePage={activePage}
        onNavigate={onNavigate}
        workflows={workflows}
        selectedWorkflowId={selectedWorkflow.id}
        onWorkflowSelect={onWorkflowSelect}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div
          style={{
            padding: "7px 22px",
            borderBottom: `1px solid ${C.bd}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: C.s1,
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            {activePage !== "dashboard" && (
              <>
                <StatusBadge tone={statusMeta.tone}>{statusMeta.label}</StatusBadge>
                <span style={{ fontSize: 12, fontWeight: 500 }}>{selectedWorkflow.name}</span>
                <span style={{ fontSize: 9, color: C.tx3, fontFamily: C.mono }}>
                  {selectedWorkflow.cozeId} → {selectedWorkflow.difyId ?? "—"}
                </span>
              </>
            )}
          </div>
          <span style={{ fontSize: 9, color: C.tx3 }}>
            {new Date().toLocaleDateString("zh-CN")}
          </span>
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: "18px 22px" }}>{children}</div>
      </div>
    </div>
  );
}
