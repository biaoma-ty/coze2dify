import { C } from "../theme";
import type { Tone } from "../types";
import { progressPercent } from "../utils";

interface ProgressBarProps {
  value: number;
  total: number;
  tone?: Tone;
}

export default function ProgressBar({
  value,
  total,
  tone = "accent",
}: ProgressBarProps) {
  const width = progressPercent(value, total);
  const color = {
    accent: C.acc,
    info: C.coze,
    success: C.ok,
    warning: C.warn,
    danger: C.err,
    muted: C.tx2,
  }[tone];

  return (
    <div
      style={{
        width: "100%",
        height: 5,
        borderRadius: 3,
        background: C.bd,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${width}%`,
          height: "100%",
          borderRadius: 3,
          background: color,
          transition: "width .5s",
        }}
      />
    </div>
  );
}
