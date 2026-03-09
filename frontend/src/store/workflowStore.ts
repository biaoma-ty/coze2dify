import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
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

type WorkflowStoreData = Omit<
  WorkflowState,
  "setSourceMethod" | "setSourceNodes" | "setConversion" | "reset"
>;

const initialState: WorkflowStoreData = {
  sourceMethod: null,
  sourceNodes: [],
  conversionId: null,
  conversionReport: null,
};

export const useWorkflowStore = create<WorkflowState>()(
  persist((set) => ({
    ...initialState,
  setSourceMethod: (method) => set({ sourceMethod: method }),
  setSourceNodes: (nodes) => set({ sourceNodes: nodes }),
  setConversion: (id, report) => set({ conversionId: id, conversionReport: report }),
  reset: () => set(initialState),
  }), {
    name: "coze2dify-workflow",
    storage: createJSONStorage(() => sessionStorage),
  }),
);
