import { useState } from "react";
import { downloadDSL } from "../../api/conversion";

export default function DownloadButton({
  conversionId,
  disabled = false,
  disabledReason = "",
}: {
  conversionId: string;
  disabled?: boolean;
  disabledReason?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDownload = async () => {
    if (disabled) {
      return;
    }
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
      <button className="btn btn-primary" onClick={handleDownload} disabled={loading || disabled}>
        {loading ? "Downloading..." : "↓ Download DSL"}
      </button>
      {!error && disabledReason && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{disabledReason}</span>
      )}
      {error && (
        <span style={{ fontSize: "0.72rem", color: "var(--c-red)" }}>{error}</span>
      )}
    </div>
  );
}
