import DevModeBanner from "../components/devmode/DevModeBanner";
import PlatformConnectPanel from "../components/browser/PlatformConnectPanel";
import WorkflowBrowser from "../components/browser/WorkflowBrowser";

export default function BrowsePage() {
  return (
    <div className="fade-in">
      <DevModeBanner />

      <div className="page-header">
        <h1 className="page-title">Browse Platform Workflows</h1>
        <p className="page-description">
          Connect to Coze and Dify to browse, select, and migrate workflows directly from the platform
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <PlatformConnectPanel />
        <WorkflowBrowser />
      </div>
    </div>
  );
}
