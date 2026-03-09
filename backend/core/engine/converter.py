from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.dify.models import DifyDSL
from core.ir.models import ConversionReport, IRWorkflow, NodeConversionResult
from core.mapper.node_mapper import NodeMapper


class ConversionEngine:
    """Orchestrates the full conversion pipeline."""

    def __init__(self) -> None:
        self.coze_parser = CozeParser()
        self.dify_generator = DifyGenerator()
        self.node_mapper = NodeMapper()

    def convert_from_json(self, content: str | bytes, fmt: str = "json") -> tuple[DifyDSL, ConversionReport]:
        ir_workflow = self.coze_parser.parse_file(content, fmt)
        return self.convert_from_ir(ir_workflow)

    def convert_from_dict(self, data: dict) -> tuple[DifyDSL, ConversionReport]:
        ir_workflow = self.coze_parser.parse_dict(data)
        return self.convert_from_ir(ir_workflow)

    def convert_from_ir(self, ir_workflow: IRWorkflow) -> tuple[DifyDSL, ConversionReport]:
        report = self._build_report(ir_workflow)
        dify_dsl = self.dify_generator.generate(ir_workflow)
        return dify_dsl, report

    def _build_report(self, ir_workflow: IRWorkflow) -> ConversionReport:
        results: list[NodeConversionResult] = []
        mapped = partial = unmappable = skipped = 0

        for node in ir_workflow.nodes:
            rule = self.node_mapper.get_rule(node.node_type)
            result = NodeConversionResult(
                source_node_id=node.id,
                source_node_type=node.source_type_name,
                target_node_id=node.id,
                target_node_type=rule.dify_type,
                status=rule.status,
                warnings=[rule.notes] if rule.notes else [],
            )
            results.append(result)

            match rule.status:
                case "mapped": mapped += 1
                case "partial": partial += 1
                case "unmappable": unmappable += 1
                case "skipped": skipped += 1

        return ConversionReport(
            workflow_name=ir_workflow.name,
            total_nodes=len(ir_workflow.nodes),
            mapped_count=mapped,
            partial_count=partial,
            unmappable_count=unmappable,
            skipped_count=skipped,
            node_results=results,
        )
