export type Tone = "accent" | "info" | "success" | "warning" | "danger" | "muted";

export type WorkflowStatus =
  | "verified"
  | "migrated"
  | "testing"
  | "pending"
  | "failed";

export type ComplexityLevel = "high" | "medium" | "low";

export type DagNodeType =
  | "llm"
  | "knowledge"
  | "code"
  | "condition"
  | "http"
  | "variable"
  | "start"
  | "end";

export type NodeComparisonStatus = "equivalent" | "warning" | "error";
export type Severity = "critical" | "high" | "medium" | "low";
export type Compatibility = "full" | "partial" | "custom" | "none";
export type TestStatus = "pass" | "fail";
export type ReviewVerdict = "equivalent" | "acceptable" | "not_eq" | null;
export type ReviewVerdictValue = Exclude<ReviewVerdict, null>;
export type SandboxStatus = "idle" | "starting" | "running";

export type WorkbenchPageKey =
  | "dashboard"
  | "dag"
  | "equiv"
  | "test"
  | "canary"
  | "kb"
  | "review"
  | "sandbox";

export interface WorkflowSummary {
  id: string;
  name: string;
  cozeId: string;
  difyId: string | null;
  status: WorkflowStatus;
  nodes: number;
  migrated: number;
  failed: number;
  score: number;
  complexity: ComplexityLevel;
  lastSync: string | null;
}

export interface StatusMeta {
  label: string;
  tone: Tone;
}

export interface DagNode {
  id: string;
  type: DagNodeType;
  label: string;
  x: number;
  y: number;
}

export interface DagGraphData {
  nodes: DagNode[];
  edges: Array<[string, string]>;
}

export interface NodeConfigDiff {
  field: string;
  coze: string;
  dify: string;
  sev: Exclude<Severity, "critical">;
}

export interface NodeComparison {
  id: string;
  type: DagNodeType;
  name: string;
  cCfg: Record<string, string | number | boolean>;
  dCfg: Record<string, string | number | boolean>;
  status: NodeComparisonStatus;
  diff: NodeConfigDiff[];
}

export interface PromptLine {
  ln: number;
  text: string;
  t: "same" | "removed" | "added";
}

export interface PromptFlag {
  desc: string;
  sev: Exclude<Severity, "critical">;
  impact: string;
}

export interface PromptDiffData {
  coze: PromptLine[];
  dify: PromptLine[];
  flags: PromptFlag[];
}

export interface VariableMapping {
  coze: string;
  dify: string;
  status: "mapped" | "unmapped";
  auto: boolean;
}

export interface PluginCompatibilityItem {
  coze: string;
  dify: string;
  compat: Compatibility;
}

export interface TestCase {
  id: string;
  name: string;
  input: string;
  cOut: string;
  dOut: string;
  sim: number;
  status: TestStatus;
  cL: number;
  dL: number;
  ep?: string;
}

export interface ErrorPattern {
  id: string;
  name: string;
  key: string;
  count: number;
  sev: "critical" | "high";
  desc: string;
  fix: string;
  tests: string[];
}

export interface KnowledgeBaseRecord {
  name: string;
  cC: number;
  dC: number;
  match: number;
  emb: string;
  ok: boolean;
}

export interface CanaryStage {
  pct: number;
  label: string;
  st: "done" | "active" | "pending";
  ts: string;
}

export interface RollbackVersion {
  ver: string;
  ts: string;
  st: "archived" | "rollback" | "active";
  score: number;
}

export interface ReviewItem {
  id: string;
  testId: string;
  q: string;
  sim: number;
  cS: string;
  dS: string;
  verdict: ReviewVerdict;
}

export interface StructureDiffItem {
  text: string;
  sev: Exclude<Severity, "critical">;
}

export interface SandboxMessage {
  id: string;
  role: "user" | "assistant" | "coze" | "dify";
  text: string;
  latencyMs?: number;
}

export interface LiveMetric {
  label: string;
  coze: string;
  dify: string;
}

export interface WorkbenchOverviewSummary {
  totalWorkflows: number;
  verifiedWorkflows: number;
  averageScore: number;
  totalNodes: number;
  migratedNodes: number;
  failedNodes: number;
  pendingReviews: number;
}

export interface WorkbenchOverviewResponse {
  summary: WorkbenchOverviewSummary;
  workflows: WorkflowSummary[];
}

export interface TopologyData {
  coze: DagGraphData;
  dify: DagGraphData;
  diffs: StructureDiffItem[];
}

export interface EquivalenceData {
  nodes: NodeComparison[];
  prompt: PromptDiffData;
  promptSimilarity: number;
  variables: VariableMapping[];
  plugins: PluginCompatibilityItem[];
}

export interface TestingData {
  cases: TestCase[];
  patterns: ErrorPattern[];
  generated?: number;
  executed?: number;
  lastRunAt?: string;
}

export interface KnowledgeData {
  records: KnowledgeBaseRecord[];
}

export interface ReviewData {
  items: ReviewItem[];
}

export interface ReleaseData {
  traffic: number;
  stages: CanaryStage[];
  versions: RollbackVersion[];
}

export interface SandboxData {
  status: SandboxStatus;
  messages: SandboxMessage[];
  metrics: LiveMetric[];
}
