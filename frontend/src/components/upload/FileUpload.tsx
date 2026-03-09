import { useCallback, useState } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  accept?: string;
}

export default function FileUpload({ onFileSelected, accept = ".json,.yaml,.yml" }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        setFileName(file.name);
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onFileSelected(file);
    }
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      onClick={() => document.getElementById("file-input")?.click()}
      className="card card--interactive"
      style={{
        border: `2px dashed ${dragOver ? "var(--c-accent)" : "var(--c-border)"}`,
        borderRadius: "var(--radius-lg)",
        padding: "56px 40px",
        textAlign: "center",
        cursor: "pointer",
        background: dragOver ? "var(--c-accent-glow)" : "var(--c-surface-1)",
        transition: "all 0.3s ease",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative grid pattern */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "radial-gradient(circle at 1px 1px, var(--c-border-subtle) 1px, transparent 0)",
          backgroundSize: "24px 24px",
          opacity: dragOver ? 0.6 : 0.3,
          transition: "opacity 0.3s ease",
          pointerEvents: "none",
        }}
      />

      <input id="file-input" type="file" accept={accept} onChange={handleChange} style={{ display: "none" }} />

      <div style={{ position: "relative", zIndex: 1 }}>
        {fileName ? (
          <div>
            <div style={{ fontSize: "2rem", marginBottom: 12 }}>✅</div>
            <p style={{
              margin: 0,
              fontWeight: 700,
              fontFamily: "var(--font-mono)",
              fontSize: "0.9rem",
              color: "var(--c-accent)",
            }}>
              {fileName}
            </p>
            <p style={{ margin: "8px 0 0", fontSize: "0.78rem", color: "var(--c-text-tertiary)" }}>
              Click to select a different file
            </p>
          </div>
        ) : (
          <>
            <div style={{ fontSize: "2.5rem", marginBottom: 16, opacity: 0.6 }}>📄</div>
            <p style={{
              margin: 0,
              fontSize: "0.95rem",
              fontWeight: 600,
              color: "var(--c-text-primary)",
            }}>
              Drop your Coze workflow file here
            </p>
            <p style={{
              margin: "8px 0 0",
              fontSize: "0.8rem",
              color: "var(--c-text-tertiary)",
            }}>
              Supports <span style={{ fontFamily: "var(--font-mono)", color: "var(--c-text-secondary)" }}>.json</span>
              {" "}and{" "}
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--c-text-secondary)" }}>.yaml</span>
              {" "}formats — or click to browse
            </p>
          </>
        )}
      </div>
    </div>
  );
}
