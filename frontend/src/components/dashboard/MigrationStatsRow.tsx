import { useTranslation } from "react-i18next";

interface MigrationStatsRowProps {
  total: number;
  successRate: number;
  writtenCount: number;
  pendingReview: number;
}

export default function MigrationStatsRow({
  total,
  successRate,
  writtenCount,
  pendingReview,
}: MigrationStatsRowProps) {
  const { t } = useTranslation();

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 16,
      }}
    >
      <div className="stat-card stat-card--accent">
        <div className="stat-card__value">{total}</div>
        <div className="stat-card__label">
          {t("dashboard.stats.totalConversions")}
        </div>
      </div>

      <div className={`stat-card ${successRate >= 80 ? "stat-card--green" : successRate >= 50 ? "stat-card--amber" : "stat-card--red"}`}>
        <div className="stat-card__value">{successRate}%</div>
        <div className="stat-card__label">
          {t("dashboard.stats.successRate")}
        </div>
      </div>

      <div className="stat-card stat-card--green">
        <div className="stat-card__value">{writtenCount}</div>
        <div className="stat-card__label">
          {t("dashboard.stats.writtenToDify")}
        </div>
      </div>

      <div className="stat-card stat-card--blue">
        <div className="stat-card__value">{pendingReview}</div>
        <div className="stat-card__label">
          {t("dashboard.stats.pendingReview")}
        </div>
      </div>
    </div>
  );
}
