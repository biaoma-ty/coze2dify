from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from core.ir.models import IREdge, IRNode, IRWorkflow


@dataclass(slots=True)
class GraphValidationResult:
    errors: list[str] = field(default_factory=list)


class IRGraphValidator:
    """Validates structural graph invariants that are independent of node mapping support."""

    def validate(self, workflow: IRWorkflow) -> GraphValidationResult:
        result = GraphValidationResult()
        all_nodes: dict[str, IRNode] = {}
        self._collect_nodes(workflow.nodes, all_nodes, result)

        top_level_ids = {node.id for node in workflow.nodes}
        result.errors.extend(
            self._validate_edges(
                workflow.edges,
                valid_node_ids=top_level_ids,
                context="workflow",
            )
        )
        if self._has_cycle(top_level_ids, workflow.edges):
            result.errors.append(
                "Workflow graph contains a top-level cycle; only acyclic top-level graphs are supported."
            )

        for node in workflow.nodes:
            self._validate_composite(node, result)

        result.errors = list(dict.fromkeys(error for error in result.errors if error))
        return result

    def _collect_nodes(
        self,
        nodes: list[IRNode],
        all_nodes: dict[str, IRNode],
        result: GraphValidationResult,
    ) -> None:
        for node in nodes:
            if node.id in all_nodes:
                result.errors.append(f"Duplicate node id '{node.id}' found in workflow graph.")
            else:
                all_nodes[node.id] = node
            if node.children:
                self._collect_nodes(node.children, all_nodes, result)

    def _validate_composite(self, node: IRNode, result: GraphValidationResult) -> None:
        if node.children or node.child_edges:
            valid_child_ids = {node.id}
            valid_child_ids.update(self._descendant_ids(node.children))
            result.errors.extend(
                self._validate_edges(
                    node.child_edges,
                    valid_node_ids=valid_child_ids,
                    context=f"composite node '{node.id}'",
                )
            )

        for child in node.children:
            self._validate_composite(child, result)

    def _descendant_ids(self, nodes: list[IRNode]) -> set[str]:
        ids: set[str] = set()
        for node in nodes:
            ids.add(node.id)
            if node.children:
                ids.update(self._descendant_ids(node.children))
        return ids

    @staticmethod
    def _validate_edges(edges: list[IREdge], *, valid_node_ids: set[str], context: str) -> list[str]:
        errors: list[str] = []
        for edge in edges:
            if edge.source_node_id not in valid_node_ids:
                errors.append(f"{context.capitalize()} edge references missing source node '{edge.source_node_id}'.")
            if edge.target_node_id not in valid_node_ids:
                errors.append(f"{context.capitalize()} edge references missing target node '{edge.target_node_id}'.")
        return errors

    @staticmethod
    def _has_cycle(node_ids: set[str], edges: list[IREdge]) -> bool:
        indegree = {node_id: 0 for node_id in node_ids}
        outgoing: dict[str, list[str]] = defaultdict(list)
        for edge in edges:
            if edge.source_node_id not in node_ids or edge.target_node_id not in node_ids:
                continue
            outgoing[edge.source_node_id].append(edge.target_node_id)
            indegree[edge.target_node_id] += 1

        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for target in outgoing[current]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)

        return visited != len(node_ids)
