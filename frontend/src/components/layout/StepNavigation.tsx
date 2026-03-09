const steps = [
  { label: "Source", icon: "📂" },
  { label: "Mapping", icon: "🔗" },
  { label: "Preview", icon: "👁" },
  { label: "Export", icon: "🚀" },
];

interface Props {
  currentStep: number;
}

export default function StepNavigation({ currentStep }: Props) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 32 }}>
      {steps.map((step, i) => {
        const isActive = i === currentStep;
        const isDone = i < currentStep;
        const isLast = i === steps.length - 1;

        return (
          <div key={step.label} style={{ display: "flex", alignItems: "center" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 16px",
                borderRadius: 8,
                background: isActive ? "var(--c-accent-dim)" : isDone ? "var(--c-green-dim)" : "transparent",
                border: `1px solid ${isActive ? "var(--c-accent)" : isDone ? "#10b98130" : "var(--c-border-subtle)"}`,
                transition: "all 0.3s ease",
              }}
            >
              <div
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 6,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.65rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  background: isActive ? "var(--c-accent)" : isDone ? "var(--c-green)" : "var(--c-surface-3)",
                  color: isActive || isDone ? "var(--c-void)" : "var(--c-text-tertiary)",
                }}
              >
                {isDone ? "✓" : i + 1}
              </div>
              <span
                style={{
                  fontSize: "0.78rem",
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "var(--c-accent)" : isDone ? "var(--c-green)" : "var(--c-text-tertiary)",
                  fontFamily: "var(--font-body)",
                }}
              >
                {step.label}
              </span>
            </div>

            {!isLast && (
              <div
                style={{
                  width: 32,
                  height: 1,
                  background: isDone ? "var(--c-green)" : "var(--c-border-subtle)",
                  margin: "0 4px",
                  transition: "background 0.3s ease",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
