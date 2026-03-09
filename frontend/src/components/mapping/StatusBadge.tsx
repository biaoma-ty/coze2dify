import type { MappingStatus } from "../../types/ir";

const classMap: Record<MappingStatus, string> = {
  mapped: "badge badge--mapped",
  partial: "badge badge--partial",
  unmappable: "badge badge--unmappable",
  skipped: "badge badge--skipped",
};

export default function StatusBadge({ status }: { status: MappingStatus }) {
  return <span className={classMap[status]}>{status}</span>;
}
