/* ── Coze ── */

export interface CozeWorkspace {
  id: string;
  name: string;
}

export interface CozeWorkflowItem {
  bot_id: string;
  bot_name: string;
  description: string;
  publish_time: string;
}

/* ── Dify ── */

export interface DifyAppItem {
  app_id: string;
  name: string;
  mode: string;
  description: string;
  workflow_id?: string;
  created_at: string;
  updated_at: string;
}

/* ── Dev Mode ── */

export interface DetectedService {
  name: string;
  path: string;
  db_url: string;
  api_url: string;
  docker_compose_found: boolean;
  env_file_found: boolean;
}

export interface DevModeStatus {
  enabled: boolean;
  detected: {
    coze: DetectedService[];
    dify: DetectedService[];
  };
}

export interface DevModeConnectResult {
  results: {
    coze: Array<{
      name: string;
      path: string;
      db_url: string;
      api_url: string;
      db_connected?: boolean;
      db_error?: string;
      api_connected?: boolean;
    }>;
    dify: Array<{
      name: string;
      path: string;
      db_url: string;
      api_url: string;
      db_connected?: boolean;
      db_error?: string;
      api_connected?: boolean;
    }>;
  };
}
