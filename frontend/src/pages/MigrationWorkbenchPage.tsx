import { useState } from "react";
import WorkbenchShell from "../features/migrationWorkbench/components/WorkbenchShell";
import { REVIEW_QUEUE, WORKFLOWS } from "../features/migrationWorkbench/mockData";
import type {
  ReviewItem,
  WorkbenchPageKey,
} from "../features/migrationWorkbench/types";
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
  const [activePage, setActivePage] = useState<WorkbenchPageKey>("dashboard");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(WORKFLOWS[0]?.id ?? "");
  const [reviewQueue, setReviewQueue] = useState<ReviewItem[]>(REVIEW_QUEUE);

  const selectedWorkflow =
    WORKFLOWS.find((workflow) => workflow.id === selectedWorkflowId) ?? WORKFLOWS[0];

  const handleInspectWorkflow = (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setActivePage("equiv");
  };

  return (
    <div className="mw-root">
      <WorkbenchShell
        activePage={activePage}
        onNavigate={setActivePage}
        workflows={WORKFLOWS}
        selectedWorkflow={selectedWorkflow}
        onWorkflowSelect={setSelectedWorkflowId}
      >
        {renderPage(
          activePage,
          selectedWorkflow.id,
          reviewQueue,
          setReviewQueue,
          handleInspectWorkflow,
        )}
      </WorkbenchShell>
    </div>
  );
}

function renderPage(
  page: WorkbenchPageKey,
  workflowId: string,
  reviewQueue: ReviewItem[],
  setReviewQueue: React.Dispatch<React.SetStateAction<ReviewItem[]>>,
  onInspectWorkflow: (workflowId: string) => void,
) {
  const workflow = WORKFLOWS.find((item) => item.id === workflowId) ?? WORKFLOWS[0];

  switch (page) {
    case "dashboard":
      return (
        <OverviewView
          onInspectWorkflow={onInspectWorkflow}
          reviewQueue={reviewQueue}
          workflows={WORKFLOWS}
        />
      );
    case "dag":
      return <TopologyView workflow={workflow} />;
    case "equiv":
      return <EquivalenceView workflow={workflow} />;
    case "test":
      return <TestingView workflow={workflow} />;
    case "canary":
      return <ReleaseView workflow={workflow} />;
    case "kb":
      return <KnowledgeView workflow={workflow} />;
    case "review":
      return (
        <ReviewView
          reviewQueue={reviewQueue}
          setReviewQueue={setReviewQueue}
          workflow={workflow}
        />
      );
    case "sandbox":
      return <SandboxView workflow={workflow} />;
    default:
      return (
        <OverviewView
          onInspectWorkflow={onInspectWorkflow}
          reviewQueue={reviewQueue}
          workflows={WORKFLOWS}
        />
      );
  }
}
