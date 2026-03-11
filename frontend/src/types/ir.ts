import type { DatabaseTargetRef } from "./audit";

export type MappingStatus = "mapped" | "partial" | "unmappable" | "skipped";
export type SupportState = "supported" | "blocked" | "manual_review";

export interface NodeConversionResult {
  source_node_id: string;
  source_node_type: string;
  target_node_id: string | null;
  target_node_type: string | null;
  status: MappingStatus;
  support_state: SupportState;
  support_reasons: string[];
  warnings: string[];
  errors: string[];
}

export interface ConversionReport {
  support_mode: "strict_supported_subset";
  supported: boolean;
  requires_manual_review: boolean;
  blocking_issues: string[];
  manual_review_reasons: string[];
  workflow_name: string;
  total_nodes: number;
  mapped_count: number;
  partial_count: number;
  unmappable_count: number;
  skipped_count: number;
  node_results: NodeConversionResult[];
  warnings: string[];
  errors: string[];
}

export interface WorkflowNode {
  id: string;
  type: string;
  title: string;
}

export interface WorkflowGraphNodeSummary {
  id: string;
  type: string;
  title: string;
  parent_id: string | null;
}

export interface WorkflowGraphSummary {
  node_count: number;
  edge_count: number;
  nodes: WorkflowGraphNodeSummary[];
}

export interface UploadResult {
  workflow_id: string;
  node_count: number;
  edge_count: number;
  nodes: WorkflowNode[];
}

export interface ConversionResult {
  conversion_id: string;
  report: ConversionReport;
}

export interface WriteResult {
  app_id: string | null;
  mode: "create" | "update";
  status: "succeeded" | "failed";
  error?: string | null;
  requested_app_id?: string | null;
  target?: DatabaseTargetRef | null;
  written_at?: string;
}

export interface ConversionAudit {
  source: {
    type: string;
    workflow_id: string;
    workflow_name: string;
  };
  sync?: {
    sync_config_id: number;
    sync_config_name: string | null;
  } | null;
  last_write?: WriteResult | null;
}

export interface ConversionHistoryReportSummary {
  workflow_name: string;
  supported: boolean;
  requires_manual_review: boolean;
  total_nodes: number;
  mapped_count: number;
  partial_count: number;
  unmappable_count: number;
  skipped_count: number;
  warnings_count: number;
  errors_count: number;
}

export interface ConversionHistoryItem {
  conversion_id: string;
  status: string;
  source_type: string;
  source_workflow_id: string;
  source_workflow_name: string;
  created_at: string | null;
  completed_at: string | null;
  write_result: WriteResult | null;
  audit: ConversionAudit | null;
  error_message: string | null;
  report_summary: ConversionHistoryReportSummary | null;
}

export interface ConversionHistoryResponse {
  items: ConversionHistoryItem[];
  total: number;
}

export interface ConversionDetail {
  conversion_id: string;
  status: string;
  source_type: string;
  source_workflow_id: string;
  source_workflow_name: string;
  dsl: Record<string, unknown>;
  source_graph: WorkflowGraphSummary | null;
  target_graph: WorkflowGraphSummary | null;
  report: ConversionReport;
  write_result: WriteResult | null;
  audit: ConversionAudit | null;
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
}
