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
    blocking_issues: list[str] = field(default_factory=list)
    node_decisions: dict[str, NodeSupportDecision] = field(default_factory=dict)


class StrictSupportSubsetPolicy:
    """Enforces a deliberately small, high-confidence migration subset."""

    def assess_workflow(self, workflow: IRWorkflow, *, rules: dict[IRNodeType, MappingRule]) -> WorkflowSupportDecision:
        node_decisions: dict[str, NodeSupportDecision] = {}
        blocking_issues: list[str] = []

        for node in self._iter_nodes(workflow.nodes):
            decision = self.assess_node(node, rule=rules[node.node_type])
            node_decisions[node.id] = decision
            blocking_issues.extend(decision.errors)

        return WorkflowSupportDecision(
            supported=not blocking_issues,
            blocking_issues=self._dedupe(blocking_issues),
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
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
