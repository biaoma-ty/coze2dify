import { useState } from "react";
import { downloadDSL } from "../../api/conversion";

export default function DownloadButton({ conversionId }: { conversionId: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDownload = async () => {
    setLoading(true);
    setError("");
    try {
      const blob = await downloadDSL(conversionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `workflow_${conversionId}.yml`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Download failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 6 }}>
      <button className="btn btn-primary" onClick={handleDownload} disabled={loading}>
        {loading ? "Downloading..." : "↓ Download DSL"}
      </button>
      {error && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{error}</span>
      )}
    </div>
  );
}
