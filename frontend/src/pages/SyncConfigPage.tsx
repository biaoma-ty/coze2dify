import { useTranslation } from "react-i18next";
import { Settings } from "lucide-react";
import PageShell from "../components/common/PageShell";
import EmptyState from "../components/common/EmptyState";

export default function SyncConfigPage() {
  const { t } = useTranslation();

  return (
    <PageShell
      breadcrumb={[
        { label: t("nav.dashboard"), to: "/" },
        { label: t("nav.sync"), to: "/sync" },
        { label: t("sync.config.title") },
      ]}
      title={t("sync.config.title")}
      subtitle={t("sync.config.subtitle")}
    >
      <div className="card" style={{ padding: 32, marginTop: 16 }}>
        <EmptyState
          icon={Settings}
          text="Coming soon - config extracted from sync page"
        />
      </div>
    </PageShell>
  );
}
