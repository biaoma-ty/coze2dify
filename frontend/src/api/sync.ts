import client from "./client";
import type {
  SyncConfig,
  SyncConfigInput,
  SyncConnectionResult,
  SyncConflictStrategy,
  SyncDiffPreview,
  SyncHistoryEntry,
  SyncRunDetail,
  SyncScheduleInput,
  SyncScheduledJob,
  SyncStatus,
} from "../types/sync";

export async function getSyncConfig(): Promise<SyncConfig | null> {
  const { data } = await client.get<{ config: SyncConfig | null }>("/sync/config");
  return data.config;
}

export async function saveSyncConfig(payload: SyncConfigInput): Promise<SyncConfig> {
  const { data } = await client.post<{ config: SyncConfig }>("/sync/config", payload);
  return data.config;
}

export async function testSyncConnections(payload: SyncConfigInput): Promise<SyncConnectionResult> {
  const { data } = await client.post<SyncConnectionResult>("/sync/config/test", payload);
  return data;
}

export async function executeManualSync(payload: SyncConfigInput): Promise<SyncRunDetail> {
  const { data } = await client.post<SyncRunDetail>("/sync/execute", payload);
  return data;
}

export async function listSyncHistory(limit = 20): Promise<SyncHistoryEntry[]> {
  const { data } = await client.get<{ history: SyncHistoryEntry[] }>("/sync/history", {
    params: { limit },
  });
  return data.history;
}

export async function getSyncHistoryDetail(historyId: string): Promise<SyncRunDetail> {
  const { data } = await client.get<SyncRunDetail>(`/sync/history/${historyId}`);
  return data;
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const { data } = await client.get<SyncStatus>("/sync/status");
  return data;
}

export async function saveSyncSchedule(
  payload: SyncScheduleInput,
): Promise<{ config: SyncConfig; schedule: SyncScheduledJob }> {
  const { data } = await client.post<{ config: SyncConfig; schedule: SyncScheduledJob }>("/sync/schedule", payload);
  return data;
}

export async function cancelSyncSchedule(configId: number): Promise<{ config: SyncConfig; cancelled: boolean }> {
  const { data } = await client.delete<{ config: SyncConfig; cancelled: boolean }>("/sync/schedule", {
    params: { config_id: configId },
  });
  return data;
}

export async function previewSyncDiff(payload: SyncConfigInput): Promise<SyncDiffPreview> {
  const { data } = await client.post<SyncDiffPreview>("/sync/diff", payload);
  return data;
}

export async function resolveSyncConflict(
  conflictId: string,
  payload: { history_id: string; strategy: SyncConflictStrategy },
): Promise<SyncRunDetail> {
  const { data } = await client.post<SyncRunDetail>(`/sync/conflicts/${conflictId}/resolve`, payload);
  return data;
}
