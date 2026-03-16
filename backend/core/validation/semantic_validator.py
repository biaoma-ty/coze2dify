from __future__ import annotations

from dataclasses import dataclass, field

from core.ir.models import IRBranch, IRCondition, IRNode, IRVariable, IRWorkflow
from core.ir.types import ErrorStrategy, IRNodeType


@dataclass(slots=True)
class SemanticValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class IRSemanticValidator:
    """Rejects workflows whose state semantics cannot be represented safely."""

    def validate(self, workflow: IRWorkflow) -> SemanticValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        global_definitions = {(variable.scope, variable.name) for variable in workflow.global_variables}

        for variable in workflow.global_variables:
            if variable.scope == "global_user" and workflow.mode != "chatflow":
                errors.append(
                    f"Conversation variable '{variable.name}' requires chatflow mode in Dify; "
                    "workflow-mode migration would lose scope semantics."
                )

        for ref_scope, ref_name in self._iter_global_references(workflow.nodes):
            if ref_scope == "global_system":
                continue

            if ref_scope == "global_user" and workflow.mode != "chatflow":
                errors.append(
                    f"Conversation variable reference '{ref_name}' requires chatflow mode in Dify; "
                    "workflow-mode migration would be invalid."
                )

            if (ref_scope, ref_name) not in global_definitions:
                errors.append(
                    f"Global variable reference '{ref_name}' with scope '{ref_scope}' is not declared at the workflow level."
                )

        for node in self._iter_nodes(workflow.nodes):
            if not node.error_handling.enabled:
                continue
            errors.extend(self._validate_error_handling(node))

        return SemanticValidationResult(
            errors=self._dedupe(errors),
            warnings=self._dedupe(warnings),
        )

    @staticmethod
    def _iter_nodes(nodes: list[IRNode]) -> list[IRNode]:
        flattened: list[IRNode] = []
        for node in nodes:
            flattened.append(node)
            if node.children:
                flattened.extend(IRSemanticValidator._iter_nodes(node.children))
        return flattened

    def _iter_global_references(self, nodes: list[IRNode]) -> list[tuple[str, str]]:
        refs: list[tuple[str, str]] = []
        for node in nodes:
            refs.extend(self._collect_variable_refs(node.inputs))
            refs.extend(self._collect_variable_refs(node.outputs))
            refs.extend(self._collect_branch_refs(node.branches))
            if node.children:
                refs.extend(self._iter_global_references(node.children))
        return refs

    @staticmethod
    def _collect_variable_refs(variables: list[IRVariable]) -> list[tuple[str, str]]:
        refs: list[tuple[str, str]] = []
        for variable in variables:
            if variable.ref and variable.ref.source_type != "node_output":
                refs.append((variable.ref.source_type, variable.ref.field_name))
        return refs

    @classmethod
    def _collect_branch_refs(cls, branches: list[IRBranch]) -> list[tuple[str, str]]:
        refs: list[tuple[str, str]] = []
        for branch in branches:
            for condition in branch.conditions:
                refs.extend(cls._collect_condition_refs(condition))
        return refs

    @staticmethod
    def _collect_condition_refs(condition: IRCondition) -> list[tuple[str, str]]:
        refs: list[tuple[str, str]] = []
        if condition.left.source_type != "node_output":
            refs.append((condition.left.source_type, condition.left.field_name))
        if condition.right and condition.right.ref and condition.right.ref.source_type != "node_output":
            refs.append((condition.right.ref.source_type, condition.right.ref.field_name))
        return refs

    @staticmethod
    def _validate_error_handling(node: IRNode) -> list[str]:
        if node.node_type == IRNodeType.HTTP_REQUEST and node.error_handling.strategy == ErrorStrategy.THROW:
            return []

        node_label = node.source_type_name or node.node_type.value
        return [
            f"{node_label} uses Coze error-handling strategy '{node.error_handling.strategy.value}', "
            "but this migrator only preserves THROW semantics on HTTP request nodes."
        ]

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))
