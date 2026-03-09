import { create } from "zustand";
import type { ConversionReport, WorkflowNode } from "../types/ir";

interface WorkflowState {
  sourceMethod: "upload" | "api" | "database" | null;
  sourceNodes: WorkflowNode[];
  conversionId: string | null;
  conversionReport: ConversionReport | null;
  setSourceMethod: (method: "upload" | "api" | "database") => void;
  setSourceNodes: (nodes: WorkflowNode[]) => void;
  setConversion: (id: string, report: ConversionReport) => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  sourceMethod: null,
  sourceNodes: [],
  conversionId: null,
  conversionReport: null,
  setSourceMethod: (method) => set({ sourceMethod: method }),
  setSourceNodes: (nodes) => set({ sourceNodes: nodes }),
  setConversion: (id, report) => set({ conversionId: id, conversionReport: report }),
  reset: () => set({ sourceMethod: null, sourceNodes: [], conversionId: null, conversionReport: null }),
}));
