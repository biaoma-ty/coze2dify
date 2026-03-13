import type { ReactNode } from "react";
import WorkbenchShell from "../features/migrationWorkbench/components/WorkbenchShell";
import Panel from "../features/migrationWorkbench/components/Panel";
import { C } from "../features/migrationWorkbench/theme";
import useWorkbenchData from "../features/migrationWorkbench/useWorkbenchData";
import EquivalenceView from "../features/migrationWorkbench/views/EquivalenceView";
import KnowledgeView from "../features/migrationWorkbench/views/KnowledgeView";
import OverviewView from "../features/migrationWorkbench/views/OverviewView";
import ReleaseView from "../features/migrationWorkbench/views/ReleaseView";
import ReviewView from "../features/migrationWorkbench/views/ReviewView";
import SandboxView from "../features/migrationWorkbench/views/SandboxView";
import TestingView from "../features/migrationWorkbench/views/TestingView";
import TopologyView from "../features/migrationWorkbench/views/TopologyView";
import "../features/migrationWorkbench/workbench.css";

export default function MigrationWorkbenchPage() {
  const {
    activePage,
    setActivePage,
    overview,
    overviewLoading,
    overviewError,
    selectedWorkflow,
    selectedWorkflowId,
    setSelectedWorkflowId,
    topologyState,
    equivalenceState,
    testingState,
    knowledgeState,
    reviewState,
    releaseState,
    sandboxState,
    batchMigrating,
    generatingTests,
    runningTests,
    reviewUpdatingId,
    releaseUpdating,
    sandboxSending,
    handleInspectWorkflow,
    handleBatchMigrate,
    handleGenerateTests,
    handleRunTests,
    handleSetReviewVerdict,
    handleTrafficChange,
    handleRollback,
    handleStartSandbox,
    handleStopSandbox,
    handleSendSandboxMessage,
  } = useWorkbenchData();

  if (overviewLoading) {
    return (
      <div className="mw-root">
        <CenteredPanel text="正在加载迁移质检台…" />
      </div>
    );
  }

  if (overviewError || !overview || !selectedWorkflow) {
    return (
      <div className="mw-root">
        <CenteredPanel text={overviewError || "迁移质检台加载失败"} tone="danger" />
      </div>
    );
  }

  return (
    <div className="mw-root">
      <WorkbenchShell
        activePage={activePage}
        onNavigate={setActivePage}
        workflows={overview.workflows}
        selectedWorkflow={selectedWorkflow}
        onWorkflowSelect={setSelectedWorkflowId}
      >
        {renderPage({
          activePage,
          overview,
          selectedWorkflow,
          selectedWorkflowId,
          topologyState,
          equivalenceState,
          testingState,
          knowledgeState,
          reviewState,
          releaseState,
          sandboxState,
          batchMigrating,
          generatingTests,
          runningTests,
          reviewUpdatingId,
          releaseUpdating,
          sandboxSending,
          onInspectWorkflow: handleInspectWorkflow,
          onBatchMigrate: handleBatchMigrate,
          onGenerateTests: handleGenerateTests,
          onRunTests: handleRunTests,
          onSetReviewVerdict: handleSetReviewVerdict,
          onTrafficChange: handleTrafficChange,
          onRollback: handleRollback,
          onStartSandbox: handleStartSandbox,
          onStopSandbox: handleStopSandbox,
          onSendSandboxMessage: handleSendSandboxMessage,
        })}
      </WorkbenchShell>
    </div>
  );
}

interface RenderPageArgs {
  activePage: ReturnType<typeof useWorkbenchData>["activePage"];
  overview: NonNullable<ReturnType<typeof useWorkbenchData>["overview"]>;
  selectedWorkflow: NonNullable<ReturnType<typeof useWorkbenchData>["selectedWorkflow"]>;
  selectedWorkflowId: string;
  topologyState: ReturnType<typeof useWorkbenchData>["topologyState"];
  equivalenceState: ReturnType<typeof useWorkbenchData>["equivalenceState"];
  testingState: ReturnType<typeof useWorkbenchData>["testingState"];
  knowledgeState: ReturnType<typeof useWorkbenchData>["knowledgeState"];
  reviewState: ReturnType<typeof useWorkbenchData>["reviewState"];
  releaseState: ReturnType<typeof useWorkbenchData>["releaseState"];
  sandboxState: ReturnType<typeof useWorkbenchData>["sandboxState"];
  batchMigrating: boolean;
  generatingTests: boolean;
  runningTests: boolean;
  reviewUpdatingId: string | null;
  releaseUpdating: boolean;
  sandboxSending: boolean;
  onInspectWorkflow: (workflowId: string) => void;
  onBatchMigrate: () => void;
  onGenerateTests: () => void;
  onRunTests: () => void;
  onSetReviewVerdict: (
    reviewId: string,
    verdict: "equivalent" | "acceptable" | "not_eq",
  ) => void;
  onTrafficChange: (traffic: number) => void;
  onRollback: (version?: string) => void;
  onStartSandbox: () => void;
  onStopSandbox: () => void;
  onSendSandboxMessage: (text: string) => void;
}

function renderPage({
  activePage,
  overview,
  selectedWorkflow,
  selectedWorkflowId,
  topologyState,
  equivalenceState,
  testingState,
  knowledgeState,
  reviewState,
  releaseState,
  sandboxState,
  batchMigrating,
  generatingTests,
  runningTests,
  reviewUpdatingId,
  releaseUpdating,
  sandboxSending,
  onInspectWorkflow,
  onBatchMigrate,
  onGenerateTests,
  onRunTests,
  onSetReviewVerdict,
  onTrafficChange,
  onRollback,
  onStartSandbox,
  onStopSandbox,
  onSendSandboxMessage,
}: RenderPageArgs) {
  switch (activePage) {
    case "dashboard":
      return (
        <OverviewView
          summary={overview.summary}
          workflows={overview.workflows}
          onInspectWorkflow={onInspectWorkflow}
          onBatchMigrate={onBatchMigrate}
          batchMigrating={batchMigrating}
        />
      );
    case "dag":
      return renderAsyncSection(topologyState, () => (
        <TopologyView workflow={selectedWorkflow} data={topologyState.data!} />
      ));
    case "equiv":
      return renderAsyncSection(equivalenceState, () => (
        <EquivalenceView workflow={selectedWorkflow} data={equivalenceState.data!} />
      ));
    case "test":
      return renderAsyncSection(testingState, () => (
        <TestingView
          workflow={selectedWorkflow}
          data={testingState.data!}
          onGenerate={onGenerateTests}
          onRunAll={onRunTests}
          generating={generatingTests}
          running={runningTests}
        />
      ));
    case "canary":
      return renderAsyncSection(releaseState, () => (
        <ReleaseView
          workflow={selectedWorkflow}
          data={releaseState.data!}
          onTrafficChange={onTrafficChange}
          onRollback={onRollback}
          updating={releaseUpdating}
        />
      ));
    case "kb":
      return renderAsyncSection(knowledgeState, () => (
        <KnowledgeView workflow={selectedWorkflow} records={knowledgeState.data!.records} />
      ));
    case "review":
      return renderAsyncSection(reviewState, () => (
        <ReviewView
          workflow={selectedWorkflow}
          reviewQueue={reviewState.data!.items}
          onSetVerdict={onSetReviewVerdict}
          updatingId={reviewUpdatingId}
        />
      ));
    case "sandbox":
      return renderAsyncSection(sandboxState, () => (
        <SandboxView
          workflow={selectedWorkflow}
          data={sandboxState.data!}
          onStart={onStartSandbox}
          onStop={onStopSandbox}
          onSend={onSendSandboxMessage}
          sending={sandboxSending}
        />
      ));
    default:
      return (
        <OverviewView
          summary={overview.summary}
          workflows={overview.workflows}
          onInspectWorkflow={onInspectWorkflow}
          onBatchMigrate={onBatchMigrate}
          batchMigrating={batchMigrating}
        />
      );
  }
}

function renderAsyncSection<T extends { loading: boolean; error: string | null; data: unknown }>(
  state: T,
  render: () => ReactNode,
) {
  if (state.loading) {
    return <CenteredPanel text="加载中…" inset />;
  }

  if (state.error) {
    return <CenteredPanel text={state.error} inset tone="danger" />;
  }

  if (!state.data) {
    return <CenteredPanel text="暂无数据" inset />;
  }

  return render();
}

interface CenteredPanelProps {
  text: string;
  inset?: boolean;
  tone?: "default" | "danger";
}

function CenteredPanel({ text, inset = false, tone = "default" }: CenteredPanelProps) {
  return (
    <div
      style={{
        minHeight: inset ? 240 : "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: inset ? 0 : 24,
        background: inset ? "transparent" : C.bg,
      }}
    >
      <Panel style={{ padding: "24px 28px", color: tone === "danger" ? C.err : C.tx2 }}>
        {text}
      </Panel>
    </div>
  );
}
