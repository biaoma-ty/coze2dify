import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import * as Tabs from "@radix-ui/react-tabs";
import PageShell from "../components/common/PageShell";
import Skeleton from "../components/common/Skeleton";
import ConversionHistoryTable from "../components/history/ConversionHistoryTable";
import SyncHistoryTable from "../components/sync/SyncHistoryTable";
import { listConversionHistory } from "../api/conversion";
import { listSyncHistory } from "../api/sync";
import type { ConversionHistoryItem } from "../types/ir";
import type { SyncHistoryEntry } from "../types/sync";

export default function UnifiedHistoryPage() {
  const { t } = useTranslation();
  const [conversions, setConversions] = useState<ConversionHistoryItem[]>([]);
  const [syncRuns, setSyncRuns] = useState<SyncHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [conversionResponse, syncHistory] = await Promise.all([
          listConversionHistory({ limit: 50 }),
          listSyncHistory(50),
        ]);
        if (!cancelled) {
          setConversions(conversionResponse.items);
          setSyncRuns(syncHistory);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(
            e?.response?.data?.detail || e?.message || "Failed to load history",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const lastConversionDate = conversions.length > 0
    ? conversions[0].created_at
    : null;
  const lastSyncDate = syncRuns.length > 0
    ? syncRuns[0].started_at
    : null;
  const lastActivityDate = [lastConversionDate, lastSyncDate]
    .filter(Boolean)
    .sort((a, b) => new Date(b!).getTime() - new Date(a!).getTime())[0] || null;

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.history") },
      ]}
      title={t("history.title")}
      subtitle={t("history.subtitle")}
    >
      {error && (
        <div className="alert alert--error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div className="stat-card stat-card--accent">
          <div className="stat-card__value">{conversions.length}</div>
          <div className="stat-card__label">{t("history.totalConversions")}</div>
        </div>
        <div className="stat-card stat-card--blue">
          <div className="stat-card__value">{syncRuns.length}</div>
          <div className="stat-card__label">{t("history.totalSyncRuns")}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__value" style={{ fontSize: "1rem" }}>
            {lastActivityDate
              ? new Date(lastActivityDate).toLocaleDateString()
              : "--"}
          </div>
          <div className="stat-card__label">{t("history.lastActivity")}</div>
        </div>
      </div>

      {loading ? (
        <Skeleton variant="row" count={8} />
      ) : (
        <Tabs.Root defaultValue="conversions">
          <Tabs.List className="tab-bar" style={{ marginBottom: 20 }}>
            <Tabs.Trigger value="conversions" className="tab-btn">
              {t("history.tabs.conversions")} ({conversions.length})
            </Tabs.Trigger>
            <Tabs.Trigger value="syncRuns" className="tab-btn">
              {t("history.tabs.syncRuns")} ({syncRuns.length})
            </Tabs.Trigger>
          </Tabs.List>

          <Tabs.Content value="conversions" className="fade-in">
            {conversions.length === 0 ? (
              <div className="empty-state card" style={{ borderStyle: "dashed" }}>
                <p className="empty-state__text">{t("common.noResults")}</p>
              </div>
            ) : (
              <ConversionHistoryTable items={conversions} />
            )}
          </Tabs.Content>

          <Tabs.Content value="syncRuns" className="fade-in">
            <SyncHistoryTable items={syncRuns} />
          </Tabs.Content>
        </Tabs.Root>
      )}
    </PageShell>
  );
}
