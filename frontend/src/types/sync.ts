import type { DatabaseTargetRef } from "./audit";

export type SyncMode = "manual" | "scheduled";
export type SyncRunStatus = "completed" | "partial" | "failed" | "running";
export type SyncConflictStrategy = "source_wins" | "target_wins" | "manual";

export interface SyncConfig {
  id: number;
  name: string;
  coze_db_type: string;
  coze_db: DatabaseTargetRef | null;
  dify_db: DatabaseTargetRef | null;
  has_stored_coze_db_url: boolean;
  has_stored_dify_db_url: boolean;
  sync_mode: SyncMode;
  cron_expression: string | null;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface SyncConfigInput {
  config_id?: number;
  name: string;
  coze_db_type?: string;
  coze_db_url: string;
  dify_db_url: string;
  sync_mode?: SyncMode;
  cron_expression?: string | null;
}

export interface SyncScheduleInput extends SyncConfigInput {
  cron_expression: string;
}

export interface SyncConnectionCheck {
  connected: boolean;
  error: string | null;
}

export interface SyncConnectionResult {
  coze_db: SyncConnectionCheck;
  dify_db: SyncConnectionCheck;
}

export interface SyncSummary {
  created: number;
  updated: number;
  failed: number;
  skipped: number;
  unsupported: number;
  conflicts: number;
}

export interface SyncResolution {
  strategy: SyncConflictStrategy;
  resolved_at?: string;
  status: string;
}

export interface SyncRunItem {
  action: string;
  status: "created" | "updated" | "failed" | "skipped" | "unsupported" | "conflict";
  source_workflow_id: string;
  source_workflow_name: string;
  target_app_id: string | null;
  conversion_id: string | null;
  message: string;
  resolution?: SyncResolution;
}

export interface SyncScheduledJob {
  config_id: number;
  job_id: string;
  cron_expression: string;
  next_run_at: string | null;
}

export interface SyncStatus {
  status: SyncRunStatus | "idle";
  history_id: string | null;
  scheduled_jobs: SyncScheduledJob[];
}

export interface SyncRunAudit {
  config_name?: string;
  sync_mode?: string;
  cron_expression?: string | null;
  trigger_type?: string;
  source_db?: DatabaseTargetRef | null;
  target_db?: DatabaseTargetRef | null;
  failure_samples?: string[];
  last_error?: string | null;
  completed_at?: string | null;
  last_resolution?: {
    conflict_id: string;
    strategy: SyncConflictStrategy;
    status: string;
    resolved_at: string;
  } | null;
}

export interface SyncHistoryEntry {
  id: string;
  sync_config_id: number;
  sync_config_name: string | null;
  trigger_type: string;
  status: SyncRunStatus;
  started_at: string | null;
  completed_at: string | null;
  workflows_synced: number;
  workflows_failed: number;
  conflicts_count: number;
  summary: SyncSummary;
  audit?: SyncRunAudit | null;
}

export interface SyncRunDetail extends SyncHistoryEntry {
  items: SyncRunItem[];
}

export interface SyncDiffPreview {
  config_id: number;
  status: Exclude<SyncRunStatus, "running">;
  summary: SyncSummary;
  items: SyncRunItem[];
}
