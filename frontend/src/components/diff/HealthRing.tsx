interface HealthRingProps {
  mapped: number;
  partial: number;
  unmappable: number;
  skipped: number;
  size?: number;
  label?: string;
}

export default function HealthRing({
  mapped,
  partial,
  unmappable,
  skipped,
  size = 80,
  label,
}: HealthRingProps) {
  const total = mapped + partial + unmappable + skipped;
  if (total === 0) {
    return (
      <div className="health-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox="0 0 36 36">
          <circle
            cx="18" cy="18" r="15.9"
            fill="none"
            stroke="var(--c-surface-3)"
            strokeWidth="3"
          />
        </svg>
        {label && <span className="health-ring__label">{label}</span>}
      </div>
    );
  }

  const segments = [
    { value: mapped, color: "var(--c-green)" },
    { value: partial, color: "var(--c-amber)" },
    { value: unmappable, color: "var(--c-red)" },
    { value: skipped, color: "var(--c-slate)" },
  ];

  const circumference = 2 * Math.PI * 15.9;
  let offset = 0;

  return (
    <div className="health-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 36 36">
        <circle
          cx="18" cy="18" r="15.9"
          fill="none"
          stroke="var(--c-surface-3)"
          strokeWidth="3"
        />
        {segments.map((seg, i) => {
          if (seg.value === 0) return null;
          const pct = seg.value / total;
          const dashLength = pct * circumference;
          const dashGap = circumference - dashLength;
          const currentOffset = offset;
          offset += dashLength;
          return (
            <circle
              key={i}
              cx="18" cy="18" r="15.9"
              fill="none"
              stroke={seg.color}
              strokeWidth="3"
              strokeDasharray={`${dashLength} ${dashGap}`}
              strokeDashoffset={-currentOffset}
              strokeLinecap="butt"
              transform="rotate(-90 18 18)"
              style={{ transition: "stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease" }}
            />
          );
        })}
      </svg>
      {label && <span className="health-ring__label">{label}</span>}
    </div>
  );
}
