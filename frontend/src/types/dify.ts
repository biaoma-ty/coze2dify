export interface DifyDSL {
  version: string;
  kind: string;
  app: Record<string, unknown>;
  workflow: {
    graph: {
      nodes: DifyNode[];
      edges: DifyEdge[];
    };
  };
}

export interface DifyNode {
  id: string;
  data: { type: string; title: string; desc: string; extra: Record<string, unknown> };
  position: { x: number; y: number };
}

export interface DifyEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: string;
  targetHandle: string;
}
