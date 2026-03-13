import type { StatusMeta, WorkbenchPageKey } from "./types";

export const C = {
  bg: "#060a12",
  s1: "#0c1221",
  s2: "#12192d",
  s3: "#182240",
  bd: "#1c2a48",
  bdL: "#263a5a",
  tx: "#dce4f0",
  tx2: "#7889a6",
  tx3: "#4d5f7a",
  acc: "#00d4ff",
  accD: "rgba(0,212,255,0.1)",
  coze: "#4ea8ff",
  cozeD: "rgba(78,168,255,0.1)",
  dify: "#b27aff",
  difyD: "rgba(178,122,255,0.1)",
  ok: "#22dda0",
  okD: "rgba(34,221,160,0.1)",
  warn: "#ffaa3e",
  warnD: "rgba(255,170,62,0.1)",
  err: "#ff5264",
  errD: "rgba(255,82,100,0.1)",
  ft: "'JetBrains Mono','Noto Sans SC',system-ui,sans-serif",
  mono: "'JetBrains Mono','Fira Code',monospace",
} as const;

export const STATUS_MAP: Record<
  "verified" | "migrated" | "testing" | "pending" | "failed",
  StatusMeta & { color: string }
> = {
  verified: { label: "已验证", tone: "success", color: C.ok },
  migrated: { label: "已迁移", tone: "info", color: C.coze },
  testing: { label: "测试中", tone: "warning", color: C.warn },
  pending: { label: "待迁移", tone: "muted", color: C.tx2 },
  failed: { label: "失败", tone: "danger", color: C.err },
};

export const COMPLEXITY_MAP = {
  high: { label: "高", color: C.err, tone: "danger" as const },
  medium: { label: "中", color: C.warn, tone: "warning" as const },
  low: { label: "低", color: C.ok, tone: "success" as const },
};

export const NODE_LABELS = {
  llm: "LLM",
  knowledge: "KB",
  code: "CODE",
  condition: "IF",
  http: "HTTP",
  variable: "VAR",
  start: "IN",
  end: "OUT",
} as const;

export const NODE_ICONS = {
  llm: "🧠",
  knowledge: "📚",
  code: "⚡",
  condition: "🔀",
  http: "🌐",
  variable: "📦",
  start: "▶",
  end: "⏹",
} as const;

export const NODE_COLORS = {
  llm: C.coze,
  knowledge: C.ok,
  code: C.warn,
  condition: C.dify,
  http: "#fb923c",
  variable: "#f472b6",
  start: C.tx2,
  end: C.tx2,
} as const;

export const WORKBENCH_NAV: Array<{ key: WorkbenchPageKey; label: string; group: string }> = [
  { key: "dashboard", label: "迁移概览", group: "总览" },
  { key: "dag", label: "拓扑对比", group: "分析" },
  { key: "equiv", label: "等价验证", group: "分析" },
  { key: "test", label: "自动测试", group: "分析" },
  { key: "canary", label: "灰度发布", group: "运维" },
  { key: "kb", label: "知识库", group: "运维" },
  { key: "review", label: "人工审核", group: "运维" },
  { key: "sandbox", label: "沙箱环境", group: "工具" },
];
