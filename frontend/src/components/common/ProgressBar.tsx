interface ProgressBarProps {
  value?: number; // 0-100, undefined = indeterminate
  color?: string;
}

export default function ProgressBar({ value, color }: ProgressBarProps) {
  const indeterminate = value === undefined;

  return (
    <div className="progress-bar">
      <div
        className={`progress-bar__fill ${indeterminate ? "progress-bar__fill--indeterminate" : ""}`}
        style={{
          width: indeterminate ? undefined : `${Math.min(100, Math.max(0, value))}%`,
          background: color || undefined,
        }}
      />
    </div>
  );
}
