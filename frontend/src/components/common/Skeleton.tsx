interface SkeletonProps {
  variant?: "text" | "card" | "row" | "circle";
  width?: string | number;
  height?: string | number;
  count?: number;
}

export default function Skeleton({
  variant = "text",
  width,
  height,
  count = 1,
}: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map((i) => (
        <div
          key={i}
          className={`skeleton skeleton--${variant}`}
          style={{ width, height }}
        />
      ))}
    </>
  );
}
