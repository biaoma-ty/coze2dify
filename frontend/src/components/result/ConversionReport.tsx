import type { ConversionReport as Report } from "../../types/ir";

const stats = [
  { key: "mapped_count" as const, label: "Mapped", cls: "stat-card--green", color: "var(--c-green)" },
  { key: "partial_count" as const, label: "Partial", cls: "stat-card--amber", color: "var(--c-amber)" },
  { key: "unmappable_count" as const, label: "Unmappable", cls: "stat-card--red", color: "var(--c-red)" },
  { key: "skipped_count" as const, label: "Skipped", cls: "stat-card--slate", color: "var(--c-slate)" },
];

export default function ConversionReportView({ report }: { report: Report }) {
  const total = report.total_nodes;
  const pct = (n: number) => (total > 0 ? Math.round((n / total) * 100) : 0);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
      {stats.map(({ key, label, cls, color }, i) => (
        <div key={key} className={`stat-card ${cls} fade-in fade-in-${i + 1}`}>
          <div className="stat-card__value" style={{ color }}>{report[key]}</div>
          <div className="stat-card__label">
            {label} · {pct(report[key])}%
          </div>
          {/* Mini bar */}
          <div
            style={{
              marginTop: 12,
              height: 3,
              borderRadius: 2,
              background: "var(--c-surface-3)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${pct(report[key])}%`,
                height: "100%",
                background: color,
                borderRadius: 2,
                transition: "width 0.6s var(--ease-out)",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
