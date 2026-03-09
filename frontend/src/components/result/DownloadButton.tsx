import { downloadDSL } from "../../api/conversion";

export default function DownloadButton({ conversionId }: { conversionId: string }) {
  const handleDownload = async () => {
    const blob = await downloadDSL(conversionId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `workflow_${conversionId}.yml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button className="btn btn-primary" onClick={handleDownload}>
      ↓ Download DSL
    </button>
  );
}
