import { defineConfig } from "@umijs/max";

const apiProxyTarget = process.env.API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  npmClient: "npm",
  antd: {},
  esbuildMinifyIIFE: true,
  mfsu: false,
  routes: [
    { path: "/", component: "@/pages/DashboardPage" },
    { path: "/migrate", component: "@/pages/MigratePage" },
    { path: "/migrate/browse", component: "@/pages/BrowsePage" },
    { path: "/migrate/diff/:conversionId", component: "@/pages/DiffPage" },
    { path: "/migrate/result/:conversionId", component: "@/pages/ResultPage" },
    { path: "/sync", component: "@/pages/SyncPage" },
    { path: "/sync/config", component: "@/pages/SyncConfigPage" },
    { path: "/sync/history", component: "@/pages/SyncHistoryPage" },
    { path: "/sync/history/:runId", component: "@/pages/SyncRunDetailPage" },
    { path: "/history", component: "@/pages/UnifiedHistoryPage" },
    {
      path: "/history/conversion/:conversionId",
      component: "@/pages/ConversionDetailPage",
    },
    { path: "/settings", component: "@/pages/SettingsPage" },
    { path: "/workbench", component: "@/pages/MigrationWorkbenchPage" },
    { path: "/diff/:conversionId", component: "@/pages/legacy/DiffRedirectPage" },
    {
      path: "/result/:conversionId",
      component: "@/pages/legacy/ResultRedirectPage",
    },
    { path: "/mapping/:workflowId", redirect: "/migrate" },
    { path: "/browse", redirect: "/migrate/browse" },
    { path: "/*", redirect: "/" },
  ],
  proxy: {
    "/api": {
      target: apiProxyTarget,
      changeOrigin: true,
    },
  },
});
