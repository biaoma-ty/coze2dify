import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { ConversionDetail, ConversionReport, WorkflowNode } from "../types/ir";

interface WorkflowState {
  sourceMethod: "upload" | "api" | "database" | null;
  sourceNodes: WorkflowNode[];
  conversionId: string | null;
  conversionReport: ConversionReport | null;
  conversionDetail: ConversionDetail | null;
  setSourceMethod: (method: "upload" | "api" | "database") => void;
  setSourceNodes: (nodes: WorkflowNode[]) => void;
  setConversion: (id: string, report: ConversionReport, detail?: ConversionDetail | null) => void;
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
  conversionDetail: null,
};

export const useWorkflowStore = create<WorkflowState>()(
  persist((set) => ({
    ...initialState,
    setSourceMethod: (method) => set({ sourceMethod: method }),
    setSourceNodes: (nodes) => set({ sourceNodes: nodes }),
    setConversion: (id, report, detail = null) =>
      set({
        conversionId: id,
        conversionReport: report,
        conversionDetail: detail,
      }),
    reset: () => set(initialState),
  }), {
    name: "coze2dify-workflow",
    storage: createJSONStorage(() => sessionStorage),
    partialize: (state) => ({
      sourceMethod: state.sourceMethod,
      sourceNodes: state.sourceNodes,
      conversionId: state.conversionId,
      conversionReport: state.conversionReport,
    }),
  }),
);
