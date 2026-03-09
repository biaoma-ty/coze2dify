import { create } from "zustand";

interface SyncState {
  syncStatus: "idle" | "running" | "completed" | "failed";
  cozeDbConnected: boolean;
  difyDbConnected: boolean;
  setSyncStatus: (status: SyncState["syncStatus"]) => void;
  setCozeDbConnected: (v: boolean) => void;
  setDifyDbConnected: (v: boolean) => void;
}

export const useSyncStore = create<SyncState>((set) => ({
  syncStatus: "idle",
  cozeDbConnected: false,
  difyDbConnected: false,
  setSyncStatus: (status) => set({ syncStatus: status }),
  setCozeDbConnected: (v) => set({ cozeDbConnected: v }),
  setDifyDbConnected: (v) => set({ difyDbConnected: v }),
}));
