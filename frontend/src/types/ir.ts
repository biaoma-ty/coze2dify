export type MappingStatus = "mapped" | "partial" | "unmappable" | "skipped";

export interface NodeConversionResult {
  source_node_id: string;
  source_node_type: string;
  target_node_id: string | null;
  target_node_type: string | null;
  status: MappingStatus;
  warnings: string[];
  errors: string[];
}

export interface ConversionReport {
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
  app_id: string;
  mode: "create" | "update";
  db_url?: string;
  written_at?: string;
}

export interface ConversionDetail {
  conversion_id: string;
  status: string;
  source_type: string;
  source_workflow_id: string;
  source_workflow_name: string;
  dsl: Record<string, unknown>;
  report: ConversionReport;
  write_result: WriteResult | null;
  created_at: string | null;
  completed_at: string | null;
}
