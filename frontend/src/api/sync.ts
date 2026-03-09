import client from "./client";
import type {
  SyncConfig,
  SyncConfigInput,
  SyncConnectionResult,
  SyncHistoryEntry,
  SyncRunDetail,
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
