import { beforeEach, describe, expect, it, vi } from "vitest";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("../src/api/client", () => ({
  default: {
    get: getMock,
    post: postMock,
  },
}));

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
} from "../src/api/workbench";

describe("workbench api adapter", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  it("routes workbench GET requests to the expected endpoints", async () => {
    const cases = [
      {
        call: () => getWorkbenchOverview(20),
        args: ["/workbench/overview", { params: { limit: 20 } }],
      },
      {
        call: () => getWorkflowTopology("wf-1"),
        args: ["/workbench/workflows/wf-1/topology"],
      },
      {
        call: () => getWorkflowEquivalence("wf-1"),
        args: ["/workbench/workflows/wf-1/equivalence"],
      },
      {
        call: () => getWorkflowTests("wf-1"),
        args: ["/workbench/workflows/wf-1/tests"],
      },
      {
        call: () => getWorkflowKnowledge("wf-1"),
        args: ["/workbench/workflows/wf-1/knowledge"],
      },
      {
        call: () => getWorkflowReview("wf-1"),
        args: ["/workbench/workflows/wf-1/review"],
      },
      {
        call: () => getWorkflowRelease("wf-1"),
        args: ["/workbench/workflows/wf-1/release"],
      },
      {
        call: () => getWorkflowSandbox("wf-1"),
        args: ["/workbench/workflows/wf-1/sandbox"],
      },
    ] as const;

    for (const [index, testCase] of cases.entries()) {
      const payload = { index };
      getMock.mockResolvedValueOnce({ data: payload });

      await expect(testCase.call()).resolves.toEqual(payload);
      expect(getMock).toHaveBeenNthCalledWith(index + 1, ...testCase.args);
    }
  });

  it("routes workbench POST requests to the expected endpoints", async () => {
    const cases = [
      {
        call: () => batchMigrateWorkflows(),
        args: ["/workbench/batch-migrate"],
      },
      {
        call: () => generateWorkflowTests("wf-1"),
        args: ["/workbench/workflows/wf-1/tests/generate"],
      },
      {
        call: () => runWorkflowTests("wf-1"),
        args: ["/workbench/workflows/wf-1/tests/run"],
      },
      {
        call: () => updateWorkflowReviewVerdict("wf-1", "review-1", "acceptable"),
        args: ["/workbench/workflows/wf-1/review/review-1", { verdict: "acceptable" }],
      },
      {
        call: () => updateWorkflowTraffic("wf-1", 65),
        args: ["/workbench/workflows/wf-1/release/traffic", { traffic: 65 }],
      },
      {
        call: () => rollbackWorkflowRelease("wf-1", "v2"),
        args: ["/workbench/workflows/wf-1/release/rollback", { version: "v2" }],
      },
      {
        call: () => startWorkflowSandbox("wf-1"),
        args: ["/workbench/workflows/wf-1/sandbox/start"],
      },
      {
        call: () => stopWorkflowSandbox("wf-1"),
        args: ["/workbench/workflows/wf-1/sandbox/stop"],
      },
      {
        call: () => sendWorkflowSandboxMessage("wf-1", "hello"),
        args: ["/workbench/workflows/wf-1/sandbox/messages", { text: "hello" }],
      },
    ] as const;

    for (const [index, testCase] of cases.entries()) {
      const payload = { index };
      postMock.mockResolvedValueOnce({ data: payload });

      await expect(testCase.call()).resolves.toEqual(payload);
      expect(postMock).toHaveBeenNthCalledWith(index + 1, ...testCase.args);
    }
  });
});
