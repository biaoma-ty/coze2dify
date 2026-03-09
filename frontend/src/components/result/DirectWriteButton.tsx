import { useState } from "react";
import { writeToDify } from "../../api/conversion";
import { usePlatformStore } from "../../store/platformStore";

export default function DirectWriteButton({ conversionId }: { conversionId: string }) {
  const { difyDbUrl, difyApiBase, difySelectedAppId } = usePlatformStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ appId: string; mode: "create" | "update" } | null>(null);

  const handleWrite = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await writeToDify(conversionId, {
        db_url: difyDbUrl || undefined,
        app_id: difySelectedAppId || undefined,
      });
      setResult({ appId: response.app_id, mode: response.mode });
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Write to Dify failed");
    } finally {
      setLoading(false);
    }
  };

  const difyAppUrl = result && difyApiBase ? `${difyApiBase.replace(/\/$/, "")}/app/${result.appId}/workflow` : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
      <button className="btn btn-secondary" onClick={handleWrite} disabled={loading}>
        {loading ? "Writing..." : difySelectedAppId ? "🗄 Update Dify App" : "🗄 Write to Dify DB"}
      </button>
      {result && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-green)" }}>
          {result.mode === "update" ? "Updated" : "Created"} app {result.appId.slice(0, 12)}…
          {difyAppUrl && (
            <>
              {" "}
              <a href={difyAppUrl} target="_blank" rel="noreferrer">
                Open
              </a>
            </>
          )}
        </span>
      )}
      {error && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{error}</span>
      )}
    </div>
  );
}
