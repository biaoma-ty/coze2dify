import { useTranslation } from "react-i18next";
import { BarChart3 } from "lucide-react";
import type { ConversionHistoryItem } from "../../types/ir";
import EmptyState from "../common/EmptyState";

interface NodeTypeStats {
  type: string;
  total: number;
  mapped: number;
}

function aggregateNodeTypes(
  conversions: ConversionHistoryItem[],
): NodeTypeStats[] {
  const statsMap = new Map<string, { total: number; mapped: number }>();

  for (const conversion of conversions) {
    const report = conversion.report_summary;
    if (!report) continue;

    // We aggregate at the conversion level since node_results are not in the history summary.
    // We use source_type as a pseudo node-type grouping from the history items.
    const key = conversion.source_type || "unknown";
    const existing = statsMap.get(key) || { total: 0, mapped: 0 };
    existing.total += report.total_nodes;
    existing.mapped += report.mapped_count;
    statsMap.set(key, existing);
  }

  // If we only have source_type level stats, also create synthetic per-status entries
  // to show the overall coverage breakdown more usefully.
  const overall = { total: 0, mapped: 0, partial: 0, unmappable: 0 };
  for (const conversion of conversions) {
    const report = conversion.report_summary;
    if (!report) continue;
    overall.total += report.total_nodes;
    overall.mapped += report.mapped_count;
    overall.partial += report.partial_count;
    overall.unmappable += report.unmappable_count;
  }

  const result: NodeTypeStats[] = [];

  if (overall.total > 0) {
    result.push({
      type: "Fully Mapped",
      total: overall.total,
      mapped: overall.mapped,
    });
    result.push({
      type: "Partial",
      total: overall.total,
      mapped: overall.partial,
    });
    result.push({
      type: "Unmappable",
      total: overall.total,
      mapped: overall.unmappable,
    });
  }

  return result;
}

interface NodeTypeCoverageProps {
  conversions: ConversionHistoryItem[];
}

export default function NodeTypeCoverage({
  conversions,
}: NodeTypeCoverageProps) {
  const { t } = useTranslation();
  const stats = aggregateNodeTypes(conversions);

  if (stats.length === 0) {
    return (
      <EmptyState
        icon={BarChart3}
        text={t("dashboard.nodeTypeCoverageEmpty")}
      />
    );
  }

  return (
    <div className="coverage-bar">
      {stats.map((stat) => {
        const percent =
          stat.total > 0 ? Math.round((stat.mapped / stat.total) * 100) : 0;

        return (
          <div key={stat.type} className="coverage-bar__row">
            <span className="coverage-bar__label">{stat.type}</span>
            <div className="coverage-bar__track">
              <div
                className="coverage-bar__fill coverage-bar__fill--mapped"
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className="coverage-bar__percent">{percent}%</span>
          </div>
        );
      })}
    </div>
  );
}
