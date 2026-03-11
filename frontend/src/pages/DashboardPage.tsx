import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { FilePlus2, RefreshCw, FolderSearch, Calendar } from "lucide-react";
import PageShell from "../components/common/PageShell";
import Skeleton from "../components/common/Skeleton";
import HealthBanner from "../components/dashboard/HealthBanner";
import QuickActionCard from "../components/dashboard/QuickActionCard";
import ActivityTimeline from "../components/dashboard/ActivityTimeline";
import NodeTypeCoverage from "../components/dashboard/NodeTypeCoverage";
import MigrationStatsRow from "../components/dashboard/MigrationStatsRow";
import {
  useDashboardStore,
  computeDashboardStats,
} from "../store/dashboardStore";

export default function DashboardPage() {
  const { t } = useTranslation();
  const {
    recentConversions,
    recentSyncRuns,
    syncStatus,
    loading,
    error,
    refresh,
  } = useDashboardStore();

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const stats = computeDashboardStats(recentConversions);
  const scheduledJobs = syncStatus?.scheduled_jobs ?? [];

  return (
    <PageShell
      title={t("dashboard.title")}
      subtitle={t("dashboard.subtitle")}
    >
      {/* Health Banner */}
      <div style={{ marginBottom: 24 }}>
        <HealthBanner />
      </div>

      {/* Quick Actions */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 16,
          marginBottom: 32,
        }}
      >
        <QuickActionCard
          icon={FilePlus2}
          title={t("dashboard.quickActions.newMigration")}
          description={t("dashboard.quickActions.newMigrationDesc")}
          to="/migrate"
        />
        <QuickActionCard
          icon={RefreshCw}
          title={t("dashboard.quickActions.runSync")}
          description={t("dashboard.quickActions.runSyncDesc")}
          to="/sync"
        />
        <QuickActionCard
          icon={FolderSearch}
          title={t("dashboard.quickActions.browseWorkflows")}
          description={t("dashboard.quickActions.browseWorkflowsDesc")}
          to="/migrate/browse"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert--error" style={{ marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Migration Stats */}
      {loading && recentConversions.length === 0 ? (
        <div style={{ marginBottom: 32 }}>
          <Skeleton variant="card" count={4} />
        </div>
      ) : (
        <div style={{ marginBottom: 32 }}>
          <MigrationStatsRow
            total={stats.total}
            successRate={stats.successRate}
            writtenCount={stats.writtenCount}
            pendingReview={stats.pendingReview}
          />
        </div>
      )}

      {/* Two-column: Activity Timeline + Node Type Coverage */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 24,
          marginBottom: 32,
        }}
      >
        <div className="card" style={{ padding: 20 }}>
          <div className="section-title" style={{ marginBottom: 16 }}>
            {t("dashboard.recentActivity")}
          </div>
          {loading && recentConversions.length === 0 ? (
            <Skeleton variant="row" count={5} />
          ) : (
            <ActivityTimeline
              conversions={recentConversions}
              syncRuns={recentSyncRuns}
            />
          )}
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div className="section-title" style={{ marginBottom: 4 }}>
            {t("dashboard.nodeTypeCoverage")}
          </div>
          <div className="section-subtitle" style={{ marginBottom: 16 }}>
            {t("dashboard.nodeTypeCoverageDesc")}
          </div>
          {loading && recentConversions.length === 0 ? (
            <Skeleton variant="row" count={4} />
          ) : (
            <NodeTypeCoverage conversions={recentConversions} />
          )}
        </div>
      </div>

      {/* Active Sync Schedule */}
      <div className="card" style={{ padding: 20 }}>
        <div className="section-title" style={{ marginBottom: 16 }}>
          <Calendar size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
          {t("dashboard.activeSchedule")}
        </div>
        {scheduledJobs.length === 0 ? (
          <p style={{ color: "var(--c-text-tertiary)", fontSize: "0.85rem" }}>
            {t("dashboard.noActiveSchedule")}
          </p>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {scheduledJobs.map((job) => (
              <div
                key={job.job_id}
                className="card card--interactive"
                style={{ padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
              >
                <div>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--c-text-primary)" }}>
                    {job.cron_expression}
                  </span>
                  <span style={{ marginLeft: 12, fontSize: "0.8rem", color: "var(--c-text-tertiary)" }}>
                    Config #{job.config_id}
                  </span>
                </div>
                {job.next_run_at && (
                  <div style={{ fontSize: "0.8rem", color: "var(--c-accent)" }}>
                    {t("dashboard.nextRun")}: {new Date(job.next_run_at).toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
