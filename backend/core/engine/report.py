from core.ir.models import ConversionReport


def format_report(report: ConversionReport) -> str:
    lines = [
        f"Conversion Report: {report.workflow_name}",
        f"Total nodes: {report.total_nodes}",
        f"  Mapped: {report.mapped_count}",
        f"  Partial: {report.partial_count}",
        f"  Unmappable: {report.unmappable_count}",
        f"  Skipped: {report.skipped_count}",
        "",
    ]
    for r in report.node_results:
        status_icon = {"mapped": "✓", "partial": "⚠", "unmappable": "✗", "skipped": "–"}.get(r.status, "?")
        lines.append(
            f"  {status_icon} {r.source_node_type} ({r.source_node_id}) → {r.target_node_type or 'N/A'} [{r.status}]"
        )
        for w in r.warnings:
            lines.append(f"    ⚠ {w}")
    return "\n".join(lines)
