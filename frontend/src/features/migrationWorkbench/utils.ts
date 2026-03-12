import type { ReviewItem, Severity, Tone, WorkflowSummary } from "./types";

export function summarizeWorkflows(workflows: WorkflowSummary[], reviewQueue: ReviewItem[]) {
  const scored = workflows.filter((workflow) => workflow.score > 0);
  const averageScore =
    scored.reduce((total, workflow) => total + workflow.score, 0) /
    (scored.length || 1);
  const totalNodes = workflows.reduce((total, workflow) => total + workflow.nodes, 0);
  const migratedNodes = workflows.reduce(
    (total, workflow) => total + workflow.migrated,
    0,
  );
  const failedNodes = workflows.reduce((total, workflow) => total + workflow.failed, 0);

  return {
    totalWorkflows: workflows.length,
    verifiedWorkflows: workflows.filter((workflow) => workflow.status === "verified").length,
    averageScore,
    totalNodes,
    migratedNodes,
    failedNodes,
    pendingReviews: reviewQueue.filter((item) => !item.verdict).length,
  };
}

export function progressPercent(value: number, total: number) {
  if (total <= 0) {
    return 0;
  }

  return Math.min(100, Math.max(0, (value / total) * 100));
}

export function getSimilarityTone(similarity: number): Tone {
  if (similarity >= 0.85) {
    return "success";
  }
  if (similarity >= 0.5) {
    return "warning";
  }

  return "danger";
}

export function getSeverityTone(severity: Severity): Tone {
  switch (severity) {
    case "critical":
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "low":
      return "accent";
    default:
      return "muted";
  }
}

export function buildSandboxReply(text: string, platform: "coze" | "dify") {
  const prefix = platform === "coze" ? "[Coze]" : "[Dify]";
  const latencyMs =
    platform === "coze"
      ? Math.floor(800 + Math.random() * 1200)
      : Math.floor(600 + Math.random() * 1000);

  return {
    role: platform,
    text: `${prefix} ${text.slice(0, 15)}${text.length > 15 ? "…" : ""}`,
    latencyMs,
  } as const;
}

export function createMessageId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}
