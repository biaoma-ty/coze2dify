import type { Dispatch, SetStateAction } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { message } from "antd";
import {
  batchMigrateWorkflows,
  generateWorkflowTests,
  getWorkbenchOverview,
  getWorkflowEquivalence,
  getWorkflowKnowledge,
  getWorkflowRelease,
  getWorkflowReview,
  getWorkflowSandbox,
  getWorkflowTests,
  getWorkflowTopology,
  rollbackWorkflowRelease,
  runWorkflowTests,
  sendWorkflowSandboxMessage,
  startWorkflowSandbox,
  stopWorkflowSandbox,
  updateWorkflowReviewVerdict,
  updateWorkflowTraffic,
} from "../../api/workbench";
import type {
  EquivalenceData,
  KnowledgeData,
  ReleaseData,
  ReviewData,
  ReviewVerdictValue,
  SandboxData,
  TestingData,
  TopologyData,
  WorkbenchOverviewResponse,
  WorkbenchPageKey,
} from "./types";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function createAsyncState<T>(): AsyncState<T> {
  return {
    data: null,
    loading: false,
    error: null,
  };
}

function extractError(error: unknown) {
  const maybeAxios = error as { response?: { data?: { detail?: string } }; message?: string };
  return maybeAxios.response?.data?.detail || maybeAxios.message || "请求失败";
}

export default function useWorkbenchData() {
  const [activePage, setActivePage] = useState<WorkbenchPageKey>("dashboard");
  const [overview, setOverview] = useState<WorkbenchOverviewResponse | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState("");

  const [topologyState, setTopologyState] = useState<AsyncState<TopologyData>>(createAsyncState());
  const [equivalenceState, setEquivalenceState] = useState<AsyncState<EquivalenceData>>(createAsyncState());
  const [testingState, setTestingState] = useState<AsyncState<TestingData>>(createAsyncState());
  const [knowledgeState, setKnowledgeState] = useState<AsyncState<KnowledgeData>>(createAsyncState());
  const [reviewState, setReviewState] = useState<AsyncState<ReviewData>>(createAsyncState());
  const [releaseState, setReleaseState] = useState<AsyncState<ReleaseData>>(createAsyncState());
  const [sandboxState, setSandboxState] = useState<AsyncState<SandboxData>>(createAsyncState());

  const [batchMigrating, setBatchMigrating] = useState(false);
  const [generatingTests, setGeneratingTests] = useState(false);
  const [runningTests, setRunningTests] = useState(false);
  const [reviewUpdatingId, setReviewUpdatingId] = useState<string | null>(null);
  const [releaseUpdating, setReleaseUpdating] = useState(false);
  const [sandboxSending, setSandboxSending] = useState(false);
  const sandboxStartTimerRef = useRef<number | null>(null);

  const selectedWorkflow = useMemo(() => {
    if (!overview?.workflows.length) {
      return null;
    }
    return (
      overview.workflows.find((workflow) => workflow.id === selectedWorkflowId) ??
      overview.workflows[0]
    );
  }, [overview, selectedWorkflowId]);

  useEffect(() => {
    let cancelled = false;
    setOverviewLoading(true);
    setOverviewError(null);

    getWorkbenchOverview()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setOverview(payload);
        setSelectedWorkflowId((current) => current || payload.workflows[0]?.id || "");
      })
      .catch((error) => {
        if (!cancelled) {
          setOverviewError(extractError(error));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setOverviewLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      if (sandboxStartTimerRef.current) {
        window.clearTimeout(sandboxStartTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!selectedWorkflow) {
      return;
    }

    let cancelled = false;
    const workflowId = selectedWorkflow.id;

    const load = async <T,>(
      setter: Dispatch<SetStateAction<AsyncState<T>>>,
      request: () => Promise<T>,
    ) => {
      setter({ data: null, loading: true, error: null });
      try {
        const data = await request();
        if (!cancelled) {
          setter({ data, loading: false, error: null });
        }
      } catch (error) {
        if (!cancelled) {
          setter({ data: null, loading: false, error: extractError(error) });
        }
      }
    };

    switch (activePage) {
      case "dag":
        void load(setTopologyState, () => getWorkflowTopology(workflowId));
        break;
      case "equiv":
        void load(setEquivalenceState, () => getWorkflowEquivalence(workflowId));
        break;
      case "test":
        void load(setTestingState, () => getWorkflowTests(workflowId));
        break;
      case "kb":
        void load(setKnowledgeState, () => getWorkflowKnowledge(workflowId));
        break;
      case "review":
        void load(setReviewState, () => getWorkflowReview(workflowId));
        break;
      case "canary":
        void load(setReleaseState, () => getWorkflowRelease(workflowId));
        break;
      case "sandbox":
        void load(setSandboxState, () => getWorkflowSandbox(workflowId));
        break;
      default:
        break;
    }

    return () => {
      cancelled = true;
    };
  }, [activePage, selectedWorkflow]);

  const handleInspectWorkflow = (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setActivePage("equiv");
  };

  const handleBatchMigrate = async () => {
    setBatchMigrating(true);
    try {
      const payload = await batchMigrateWorkflows();
      setOverview(payload);
      message.success("批量迁移已触发");
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setBatchMigrating(false);
    }
  };

  const handleGenerateTests = async () => {
    if (!selectedWorkflow) {
      return;
    }
    setGeneratingTests(true);
    try {
      const payload = await generateWorkflowTests(selectedWorkflow.id);
      setTestingState({ data: payload, loading: false, error: null });
      message.success(payload.generated ? "已生成 1 条测试用例" : "测试用例已是最新");
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setGeneratingTests(false);
    }
  };

  const handleRunTests = async () => {
    if (!selectedWorkflow) {
      return;
    }
    setRunningTests(true);
    try {
      const payload = await runWorkflowTests(selectedWorkflow.id);
      setTestingState({ data: payload, loading: false, error: null });
      message.success(`已执行 ${payload.executed ?? payload.cases.length} 条用例`);
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setRunningTests(false);
    }
  };

  const handleSetReviewVerdict = async (reviewId: string, verdict: ReviewVerdictValue) => {
    if (!selectedWorkflow) {
      return;
    }
    setReviewUpdatingId(reviewId);
    try {
      const payload = await updateWorkflowReviewVerdict(selectedWorkflow.id, reviewId, verdict);
      setReviewState({ data: { items: payload.items }, loading: false, error: null });
      setOverview((current) =>
        current
          ? {
              ...current,
              summary: {
                ...current.summary,
                pendingReviews: payload.summary.pendingReviews,
              },
            }
          : current,
      );
      message.success("审核结果已更新");
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setReviewUpdatingId(null);
    }
  };

  const handleTrafficChange = async (traffic: number) => {
    if (!selectedWorkflow) {
      return;
    }
    setReleaseUpdating(true);
    try {
      const payload = await updateWorkflowTraffic(selectedWorkflow.id, traffic);
      setReleaseState({ data: payload, loading: false, error: null });
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setReleaseUpdating(false);
    }
  };

  const handleRollback = async (version?: string) => {
    if (!selectedWorkflow) {
      return;
    }
    setReleaseUpdating(true);
    try {
      const payload = await rollbackWorkflowRelease(selectedWorkflow.id, version);
      setReleaseState({ data: payload, loading: false, error: null });
      message.success("已回滚到目标版本");
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setReleaseUpdating(false);
    }
  };

  const handleStartSandbox = async () => {
    if (!selectedWorkflow) {
      return;
    }
    if (sandboxStartTimerRef.current) {
      window.clearTimeout(sandboxStartTimerRef.current);
    }
    setSandboxState((current) => ({
      data: current.data
        ? { ...current.data, status: "starting" }
        : { status: "starting", messages: [], metrics: [] },
      loading: false,
      error: null,
    }));
    try {
      const payload = await startWorkflowSandbox(selectedWorkflow.id);
      sandboxStartTimerRef.current = window.setTimeout(() => {
        setSandboxState({ data: payload, loading: false, error: null });
        sandboxStartTimerRef.current = null;
      }, 1500);
    } catch (error) {
      setSandboxState({ data: null, loading: false, error: extractError(error) });
      message.error(extractError(error));
    }
  };

  const handleStopSandbox = async () => {
    if (!selectedWorkflow) {
      return;
    }
    if (sandboxStartTimerRef.current) {
      window.clearTimeout(sandboxStartTimerRef.current);
      sandboxStartTimerRef.current = null;
    }
    try {
      const payload = await stopWorkflowSandbox(selectedWorkflow.id);
      setSandboxState({ data: payload, loading: false, error: null });
    } catch (error) {
      message.error(extractError(error));
    }
  };

  const handleSendSandboxMessage = async (text: string) => {
    if (!selectedWorkflow) {
      return;
    }
    setSandboxSending(true);
    try {
      const payload = await sendWorkflowSandboxMessage(selectedWorkflow.id, text);
      setSandboxState({ data: payload, loading: false, error: null });
    } catch (error) {
      message.error(extractError(error));
    } finally {
      setSandboxSending(false);
    }
  };

  return {
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
  };
}
