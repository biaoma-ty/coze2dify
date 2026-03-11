import { useState } from "react";
import { writeToDify } from "../../api/conversion";
import { usePlatformStore } from "../../store/platformStore";
import type { ConversionReport, WriteResult } from "../../types/ir";

export default function DirectWriteButton({
  conversionId,
  report,
}: {
  conversionId: string;
  report: ConversionReport;
}) {
  const { difyDbUrl, difyApiBase, difySelectedAppId } = usePlatformStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<WriteResult | null>(null);
  const blockedReason =
    report.blocking_issues[0] || "This workflow is outside the strict supported subset.";

  const handleWrite = async () => {
    if (!report.supported) {
      setError(blockedReason);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await writeToDify(conversionId, {
        db_url: difyDbUrl || undefined,
        app_id: difySelectedAppId || undefined,
      });
      setResult(response.write_result);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Write to Dify failed");
    } finally {
      setLoading(false);
    }
  };

  const difyAppUrl =
    result?.app_id && difyApiBase ? `${difyApiBase.replace(/\/$/, "")}/app/${result.app_id}/workflow` : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
      <button className="btn btn-secondary" onClick={handleWrite} disabled={loading || !report.supported}>
        {loading ? "Writing..." : difySelectedAppId ? "🗄 Update Dify App" : "🗄 Write to Dify DB"}
      </button>
      {!error && !report.supported && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{blockedReason}</span>
      )}
      {result && (
        <div style={{ display: "grid", gap: 2 }}>
          <span style={{ fontSize: "0.72rem", color: result.status === "failed" ? "var(--c-red)" : "var(--c-green)" }}>
            {result.status === "failed"
              ? result.error || "Write failed"
              : `${result.mode === "update" ? "Updated" : "Created"} app ${(result.app_id || "unknown").slice(0, 12)}…`}
            {difyAppUrl && (
              <>
                {" "}
                <a href={difyAppUrl} target="_blank" rel="noreferrer">
                  Open
                </a>
              </>
            )}
          </span>
          {result.target?.display_url && (
            <span style={{ fontSize: "0.68rem", color: "var(--c-text-tertiary)", fontFamily: "var(--font-mono)" }}>
              {result.target.display_url}
            </span>
          )}
        </div>
      )}
      {error && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{error}</span>
      )}
    </div>
  );
}
