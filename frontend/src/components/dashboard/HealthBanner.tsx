import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getSyncStatus } from "../../api/sync";

type HealthStatus = "ok" | "error" | "checking";

export default function HealthBanner() {
  const { t } = useTranslation();
  const [backendStatus, setBackendStatus] = useState<HealthStatus>("checking");

  useEffect(() => {
    let cancelled = false;

    setBackendStatus("checking");
    getSyncStatus()
      .then(() => {
        if (!cancelled) {
          setBackendStatus("ok");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBackendStatus("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const statusLabel = (status: HealthStatus): string => {
    switch (status) {
      case "ok":
        return t("dashboard.health.connected");
      case "error":
        return t("dashboard.health.disconnected");
      case "checking":
        return t("dashboard.health.checking");
    }
  };

  return (
    <div className="health-banner">
      <div className="health-banner__item">
        <span className={`health-banner__dot health-banner__dot--${backendStatus}`} />
        <span className="health-banner__label">
          {t("dashboard.health.backend")}
        </span>
        <span className="health-banner__status">{statusLabel(backendStatus)}</span>
      </div>
    </div>
  );
}
