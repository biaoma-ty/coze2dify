from __future__ import annotations

from dataclasses import dataclass, field

from core.ir.models import IRNode, IRWorkflow
from core.ir.types import IRNodeType, MappingStatus
from core.mapper.mapping_rules import MappingRule

_SUPPORTED_NODE_TYPES = {
    IRNodeType.START,
    IRNodeType.END,
    IRNodeType.OUTPUT_EMITTER,
}

_MANUAL_REVIEW_REASON_CODE = "Python code nodes are admitted only with mandatory manual review before write-to-Dify."


@dataclass(slots=True)
class NodeSupportDecision:
    status: MappingStatus
    support_state: str
    support_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkflowSupportDecision:
    supported: bool
    requires_manual_review: bool = False
    blocking_issues: list[str] = field(default_factory=list)
    manual_review_reasons: list[str] = field(default_factory=list)
    node_decisions: dict[str, NodeSupportDecision] = field(default_factory=dict)


class StrictSupportSubsetPolicy:
    """Enforces a deliberately small, high-confidence migration subset."""

    def assess_workflow(self, workflow: IRWorkflow, *, rules: dict[IRNodeType, MappingRule]) -> WorkflowSupportDecision:
        node_decisions: dict[str, NodeSupportDecision] = {}
        blocking_issues: list[str] = []
        manual_review_reasons: list[str] = []

        for node in self._iter_nodes(workflow.nodes):
            decision = self.assess_node(node, rule=rules[node.node_type])
            node_decisions[node.id] = decision
            blocking_issues.extend(decision.errors)
            if decision.support_state == "manual_review":
                manual_review_reasons.extend(decision.support_reasons or decision.warnings)

        return WorkflowSupportDecision(
            supported=not blocking_issues,
            requires_manual_review=bool(manual_review_reasons),
            blocking_issues=self._dedupe(blocking_issues),
            manual_review_reasons=self._dedupe(manual_review_reasons),
            node_decisions=node_decisions,
        )

    def assess_node(self, node: IRNode, *, rule: MappingRule) -> NodeSupportDecision:
        if node.node_type == IRNodeType.COMMENT:
            return NodeSupportDecision(
                status=rule.status,
                support_state="supported",
            )

        if node.node_type in _SUPPORTED_NODE_TYPES:
            return NodeSupportDecision(
                status=rule.status,
                support_state="supported",
            )

        if self._is_admitted_python_code(node):
            return NodeSupportDecision(
                status=rule.status,
                support_state="manual_review",
                support_reasons=[_MANUAL_REVIEW_REASON_CODE],
                warnings=[_MANUAL_REVIEW_REASON_CODE],
            )

        reason = self._unsupported_reason(node, rule)
        return NodeSupportDecision(
            status=rule.status if rule.status != MappingStatus.SKIPPED else MappingStatus.UNMAPPABLE,
            support_state="blocked",
            support_reasons=[reason],
            errors=[reason],
        )

    @staticmethod
    def _unsupported_reason(node: IRNode, rule: MappingRule) -> str:
        node_label = node.source_type_name or node.node_type.value
        if rule.status in {MappingStatus.PARTIAL, MappingStatus.UNMAPPABLE}:
            note = f" {rule.notes}." if rule.notes else ""
            return f"{node_label} is blocked by the strict supported subset because its mapping is {rule.status}.{note}"
        return f"{node_label} is not admitted to the strict supported subset yet; semantic coverage is missing."

    @staticmethod
    def _iter_nodes(nodes: list[IRNode]) -> list[IRNode]:
        flattened: list[IRNode] = []
        for node in nodes:
            flattened.append(node)
            if node.children:
                flattened.extend(StrictSupportSubsetPolicy._iter_nodes(node.children))
        return flattened

    @staticmethod
    def _is_admitted_python_code(node: IRNode) -> bool:
        if node.node_type != IRNodeType.CODE:
            return False
        language = str(node.config.get("language") or "").strip().lower()
        code = str(node.config.get("code") or "").strip()
        return language == "python3" and bool(code)

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
