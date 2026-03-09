import { create } from "zustand";

interface SyncState {
  syncStatus: "idle" | "running" | "completed" | "failed";
  setSyncStatus: (status: SyncState["syncStatus"]) => void;
}

export const useSyncStore = create<SyncState>((set) => ({
  syncStatus: "idle",
  setSyncStatus: (status) => set({ syncStatus: status }),
}));
