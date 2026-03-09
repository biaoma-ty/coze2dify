import client from "./client";
import type {
  CozeWorkspace,
  CozeWorkflowItem,
  DifyAppItem,
  DevModeStatus,
  DevModeConnectResult,
} from "../types/platform";

/* ═══════════════════  Coze  ═══════════════════ */

export async function connectCozeApi(
  token: string,
  apiBase = "https://api.coze.com",
): Promise<{ connected: boolean; workspaces: CozeWorkspace[] }> {
  const { data } = await client.post("/platform/coze/connect", {
    access_token: token,
    api_base: apiBase,
  });
  return data;
}

export async function listCozeWorkflows(
  token: string,
  apiBase: string,
  spaceId: string,
): Promise<CozeWorkflowItem[]> {
  const { data } = await client.post("/platform/coze/workflows", {
    access_token: token,
    api_base: apiBase,
    space_id: spaceId,
  });
  return data.workflows;
}

export async function fetchCozeWorkflow(
  token: string,
  apiBase: string,
  workflowId: string,
) {
  const { data } = await client.post("/platform/coze/workflows/fetch", {
    access_token: token,
    api_base: apiBase,
    workflow_id: workflowId,
  });
  return data.workflow;
}

/* ═══════════════════  Dify  ═══════════════════ */

export async function connectDifyApi(
  apiBase: string,
  apiKey: string,
): Promise<{ connected: boolean; mode: string; total: number }> {
  const { data } = await client.post("/platform/dify/connect", {
    api_base: apiBase,
    api_key: apiKey,
  });
  return data;
}

export async function listDifyApps(
  apiBase: string,
  apiKey: string,
): Promise<DifyAppItem[]> {
  const { data } = await client.post("/platform/dify/apps", {
    api_base: apiBase,
    api_key: apiKey,
  });
  return data.apps;
}

/* ═══════════════════  DB  ═══════════════════ */

export async function testDbConnection(
  platform: "coze" | "dify",
  dbUrl: string,
): Promise<{ connected: boolean }> {
  const { data } = await client.post("/platform/db/connect", {
    platform,
    db_url: dbUrl,
  });
  return data;
}

export async function listDbWorkflows(
  platform: "coze" | "dify",
  dbUrl: string,
) {
  const { data } = await client.post("/platform/db/workflows", {
    platform,
    db_url: dbUrl,
  });
  return data.workflows;
}

/* ═══════════════════  Dev Mode  ═══════════════════ */

export async function getDevModeStatus(): Promise<DevModeStatus> {
  const { data } = await client.get("/devmode/status");
  return data;
}

export async function devModeScan(): Promise<DevModeStatus> {
  const { data } = await client.get("/devmode/scan");
  return { enabled: true, detected: data.detected };
}

export async function devModeAutoConnect(): Promise<DevModeConnectResult> {
  const { data } = await client.post("/devmode/connect");
  return data;
}
