from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.dify.models import DifyDSL
from core.ir.models import ConversionReport, IRNode, IRWorkflow, NodeConversionResult
from core.ir.types import IRNodeType
from core.mapper.node_mapper import NodeMapper
from core.validation.graph_validator import IRGraphValidator
from core.validation.support_policy import StrictSupportSubsetPolicy


class ConversionEngine:
    """Orchestrates the full conversion pipeline."""

    def __init__(self) -> None:
        self.coze_parser = CozeParser()
        self.dify_generator = DifyGenerator()
        self.node_mapper = NodeMapper()
        self.graph_validator = IRGraphValidator()
        self.support_policy = StrictSupportSubsetPolicy()

    def convert_from_json(self, content: str | bytes, fmt: str = "json") -> tuple[DifyDSL | None, ConversionReport]:
        ir_workflow = self.coze_parser.parse_file(content, fmt)
        return self.convert_from_ir(ir_workflow)

    def convert_from_dict(self, data: dict) -> tuple[DifyDSL | None, ConversionReport]:
        ir_workflow = self.coze_parser.parse_dict(data)
        return self.convert_from_ir(ir_workflow)

    def convert_from_ir(self, ir_workflow: IRWorkflow) -> tuple[DifyDSL | None, ConversionReport]:
        report = self._build_report(ir_workflow)
        dify_dsl = self.dify_generator.generate(ir_workflow) if report.supported else None
        return dify_dsl, report

    def _build_report(self, ir_workflow: IRWorkflow) -> ConversionReport:
        results: list[NodeConversionResult] = []
        mapped = partial = unmappable = skipped = 0
        warnings: list[str] = []
        errors: list[str] = []
        rules = {node_type: self.node_mapper.get_rule(node_type) for node_type in IRNodeType}
        graph_validation = self.graph_validator.validate(ir_workflow)
        support_decision = self.support_policy.assess_workflow(ir_workflow, rules=rules)

        all_nodes = self._iter_nodes(ir_workflow.nodes)
        for node in all_nodes:
            rule = rules[node.node_type]
            node_support = support_decision.node_decisions[node.id]
            result = NodeConversionResult(
                source_node_id=node.id,
                source_node_type=node.source_type_name,
                target_node_id=node.id,
                target_node_type=rule.dify_type,
                status=node_support.status,
                support_state=node_support.support_state,
                support_reasons=node_support.support_reasons,
                warnings=node_support.warnings,
                errors=node_support.errors,
            )
            results.append(result)
            warnings.extend(result.warnings)
            errors.extend(result.errors)

            match result.status:
                case "mapped":
                    mapped += 1
                case "partial":
                    partial += 1
                case "unmappable":
                    unmappable += 1
                case "skipped":
                    skipped += 1

        return ConversionReport(
            supported=support_decision.supported and not graph_validation.errors,
            requires_manual_review=support_decision.requires_manual_review,
            blocking_issues=self._dedupe(support_decision.blocking_issues + graph_validation.errors),
            manual_review_reasons=support_decision.manual_review_reasons,
            workflow_name=ir_workflow.name,
            total_nodes=len(all_nodes),
            mapped_count=mapped,
            partial_count=partial,
            unmappable_count=unmappable,
            skipped_count=skipped,
            node_results=results,
            warnings=self._dedupe(warnings),
            errors=self._dedupe(errors + graph_validation.errors),
        )

    def _iter_nodes(self, nodes: list[IRNode]) -> list[IRNode]:
        flattened: list[IRNode] = []
        for node in nodes:
            flattened.append(node)
            if node.children:
                flattened.extend(self._iter_nodes(node.children))
        return flattened

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
