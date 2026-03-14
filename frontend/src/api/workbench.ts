import client from "./client";
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
} from "../features/migrationWorkbench/types";

export async function getWorkbenchOverview(limit = 50) {
  const { data } = await client.get<WorkbenchOverviewResponse>("/workbench/overview", {
    params: { limit },
  });
  return data;
}

export async function batchMigrateWorkflows() {
  const { data } = await client.post<WorkbenchOverviewResponse>("/workbench/batch-migrate");
  return data;
}

export async function getWorkflowTopology(workflowId: string) {
  const { data } = await client.get<TopologyData>(`/workbench/workflows/${workflowId}/topology`);
  return data;
}

export async function getWorkflowEquivalence(workflowId: string) {
  const { data } = await client.get<EquivalenceData>(
    `/workbench/workflows/${workflowId}/equivalence`,
  );
  return data;
}

export async function getWorkflowTests(workflowId: string) {
  const { data } = await client.get<TestingData>(`/workbench/workflows/${workflowId}/tests`);
  return data;
}

export async function generateWorkflowTests(workflowId: string) {
  const { data } = await client.post<TestingData>(
    `/workbench/workflows/${workflowId}/tests/generate`,
  );
  return data;
}

export async function runWorkflowTests(workflowId: string) {
  const { data } = await client.post<TestingData>(`/workbench/workflows/${workflowId}/tests/run`);
  return data;
}

export async function getWorkflowKnowledge(workflowId: string) {
  const { data } = await client.get<KnowledgeData>(`/workbench/workflows/${workflowId}/knowledge`);
  return data;
}

export async function getWorkflowReview(workflowId: string) {
  const { data } = await client.get<ReviewData>(`/workbench/workflows/${workflowId}/review`);
  return data;
}

export async function updateWorkflowReviewVerdict(
  workflowId: string,
  reviewId: string,
  verdict: ReviewVerdictValue,
) {
  const { data } = await client.post<{
    item: ReviewData["items"][number];
    items: ReviewData["items"];
    summary: WorkbenchOverviewResponse["summary"];
  }>(`/workbench/workflows/${workflowId}/review/${reviewId}`, { verdict });
  return data;
}

export async function getWorkflowRelease(workflowId: string) {
  const { data } = await client.get<ReleaseData>(`/workbench/workflows/${workflowId}/release`);
  return data;
}

export async function updateWorkflowTraffic(workflowId: string, traffic: number) {
  const { data } = await client.post<ReleaseData>(
    `/workbench/workflows/${workflowId}/release/traffic`,
    { traffic },
  );
  return data;
}

export async function rollbackWorkflowRelease(workflowId: string, version?: string) {
  const { data } = await client.post<ReleaseData>(
    `/workbench/workflows/${workflowId}/release/rollback`,
    { version },
  );
  return data;
}

export async function getWorkflowSandbox(workflowId: string) {
  const { data } = await client.get<SandboxData>(`/workbench/workflows/${workflowId}/sandbox`);
  return data;
}

export async function startWorkflowSandbox(workflowId: string) {
  const { data } = await client.post<SandboxData>(`/workbench/workflows/${workflowId}/sandbox/start`);
  return data;
}

export async function stopWorkflowSandbox(workflowId: string) {
  const { data } = await client.post<SandboxData>(`/workbench/workflows/${workflowId}/sandbox/stop`);
  return data;
}

export async function sendWorkflowSandboxMessage(workflowId: string, text: string) {
  const { data } = await client.post<SandboxData>(
    `/workbench/workflows/${workflowId}/sandbox/messages`,
    { text },
  );
  return data;
}
