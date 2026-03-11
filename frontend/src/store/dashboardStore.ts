import { create } from "zustand";
import { listConversionHistory } from "../api/conversion";
import { getSyncStatus, listSyncHistory } from "../api/sync";
import type { ConversionHistoryItem } from "../types/ir";
import type { SyncHistoryEntry, SyncStatus } from "../types/sync";

interface DashboardState {
  recentConversions: ConversionHistoryItem[];
  recentSyncRuns: SyncHistoryEntry[];
  syncStatus: SyncStatus | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  recentConversions: [],
  recentSyncRuns: [],
  syncStatus: null,
  loading: false,
  error: null,

  refresh: async () => {
    set({ loading: true, error: null });
    try {
      const [conversionResponse, syncStatusResult, syncHistory] =
        await Promise.all([
          listConversionHistory({ limit: 10, offset: 0 }),
          getSyncStatus(),
          listSyncHistory(10),
        ]);

      set({
        recentConversions: conversionResponse.items,
        syncStatus: syncStatusResult,
        recentSyncRuns: syncHistory,
        loading: false,
      });
    } catch (e: any) {
      set({
        loading: false,
        error:
          e?.response?.data?.detail || e?.message || "Failed to load dashboard data",
      });
    }
  },
}));

/** Computed aggregate stats derived from store state. */
export function computeDashboardStats(conversions: ConversionHistoryItem[]) {
  const total = conversions.length;
  const succeeded = conversions.filter(
    (c) => c.status === "converted" || c.status === "written" || c.status === "updated",
  ).length;
  const successRate = total > 0 ? Math.round((succeeded / total) * 100) : 0;
  const writtenCount = conversions.filter((c) => c.write_result?.app_id).length;
  const pendingReview = conversions.filter((c) => !c.write_result?.app_id && c.status !== "failed").length;

  return { total, succeeded, successRate, writtenCount, pendingReview };
}
