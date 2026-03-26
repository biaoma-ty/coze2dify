import { describe, expect, it, vi } from "vitest";
import {
  buildSandboxReply,
  getSeverityTone,
  getSimilarityTone,
  progressPercent,
  summarizeWorkflows,
} from "../src/features/migrationWorkbench/utils";
import type {
  ReviewItem,
  WorkflowSummary,
} from "../src/features/migrationWorkbench/types";

describe("migration workbench utils", () => {
  it("summarizes workflow coverage and pending reviews", () => {
    const workflows: WorkflowSummary[] = [
      {
        id: "wf-1",
        name: "Flow A",
        cozeId: "coze-1",
        difyId: "dify-1",
        status: "verified",
        nodes: 12,
        migrated: 11,
        failed: 1,
        score: 0.92,
        complexity: "medium",
        lastSync: "2026-03-26T10:00:00Z",
      },
      {
        id: "wf-2",
        name: "Flow B",
        cozeId: "coze-2",
        difyId: null,
        status: "pending",
        nodes: 8,
        migrated: 3,
        failed: 2,
        score: 0,
        complexity: "high",
        lastSync: null,
      },
      {
        id: "wf-3",
        name: "Flow C",
        cozeId: "coze-3",
        difyId: "dify-3",
        status: "verified",
        nodes: 5,
        migrated: 5,
        failed: 0,
        score: 0.58,
        complexity: "low",
        lastSync: "2026-03-25T09:00:00Z",
      },
    ];
    const reviewQueue: ReviewItem[] = [
      {
        id: "review-1",
        testId: "test-1",
        q: "Question 1",
        sim: 0.81,
        cS: "Coze",
        dS: "Dify",
        verdict: null,
      },
      {
        id: "review-2",
        testId: "test-2",
        q: "Question 2",
        sim: 0.97,
        cS: "Coze",
        dS: "Dify",
        verdict: "equivalent",
      },
    ];

    expect(summarizeWorkflows(workflows, reviewQueue)).toEqual({
      totalWorkflows: 3,
      verifiedWorkflows: 2,
      averageScore: 0.75,
      totalNodes: 25,
      migratedNodes: 19,
      failedNodes: 3,
      pendingReviews: 1,
    });
  });

  it("clamps progress percentages to a valid range", () => {
    expect(progressPercent(5, 0)).toBe(0);
    expect(progressPercent(12, 10)).toBe(100);
    expect(progressPercent(-2, 10)).toBe(0);
    expect(progressPercent(3, 8)).toBe(37.5);
  });

  it("maps similarity and severity thresholds to tones", () => {
    expect(getSimilarityTone(0.9)).toBe("success");
    expect(getSimilarityTone(0.7)).toBe("warning");
    expect(getSimilarityTone(0.2)).toBe("danger");

    expect(getSeverityTone("critical")).toBe("danger");
    expect(getSeverityTone("medium")).toBe("warning");
    expect(getSeverityTone("low")).toBe("accent");
  });

  it("builds truncated sandbox replies with platform-specific prefixes", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.5);

    expect(buildSandboxReply("1234567890123456", "coze")).toEqual({
      role: "coze",
      text: "[Coze] 123456789012345…",
      latencyMs: 1400,
    });

    expect(buildSandboxReply("short", "dify")).toEqual({
      role: "dify",
      text: "[Dify] short",
      latencyMs: 1100,
    });
  });
});
