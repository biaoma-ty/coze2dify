from __future__ import annotations

from core.ir.models import IREdge, IRNode
from core.ir.types import IRNodeType

from .models import DifyEdge

_BRANCH_PORT_MAP = {
    "true": "true",
    "false": "false",
    "exception": "fail-branch",
}

_NODE_TYPE_TO_DIFY = {
    IRNodeType.START: "start",
    IRNodeType.END: "end",
    IRNodeType.LLM: "llm",
    IRNodeType.CODE: "code",
    IRNodeType.HTTP_REQUEST: "http-request",
    IRNodeType.CONDITION: "if-else",
    IRNodeType.LOOP_COUNTED: "loop",
    IRNodeType.LOOP_ARRAY: "iteration",
    IRNodeType.LOOP_INFINITE: "loop",
    IRNodeType.BATCH: "iteration",
    IRNodeType.KNOWLEDGE_RETRIEVAL: "knowledge-retrieval",
    IRNodeType.VARIABLE_AGGREGATOR: "variable-aggregator",
    IRNodeType.VARIABLE_ASSIGNER: "assigner",
    IRNodeType.OUTPUT_EMITTER: "answer",
    IRNodeType.INTENT_DETECTOR: "question-classifier",
    IRNodeType.QUESTION_ANSWER: "human-input",
    IRNodeType.KNOWLEDGE_WRITE: "knowledge-index",
}


class EdgeBuilder:
    """Builds Dify edge list from IR edges."""

    def __init__(self, node_map: dict[str, IRNode]) -> None:
        self.node_map = node_map

    def build_edges(self, ir_edges: list[IREdge], in_loop: bool = False, in_iteration: bool = False) -> list[DifyEdge]:
        dify_edges: list[DifyEdge] = []

        for ir_edge in ir_edges:
            source_handle = self._map_source_handle(ir_edge.source_port)
            source_type = self._get_dify_type(ir_edge.source_node_id)
            target_type = self._get_dify_type(ir_edge.target_node_id)

            edge_id = f"{ir_edge.source_node_id}-{source_handle}-{ir_edge.target_node_id}-target"

            dify_edges.append(
                DifyEdge(
                    id=edge_id,
                    source=ir_edge.source_node_id,
                    target=ir_edge.target_node_id,
                    sourceHandle=source_handle,
                    targetHandle="target",
                    data={
                        "sourceType": source_type,
                        "targetType": target_type,
                        "isInIteration": in_iteration,
                        "isInLoop": in_loop,
                    },
                )
            )

        return dify_edges

    def _map_source_handle(self, port: str) -> str:
        if port in _BRANCH_PORT_MAP:
            return _BRANCH_PORT_MAP[port]
        if port.startswith("true_"):
            return port  # Will be mapped to case_id later
        return "source"

    def _get_dify_type(self, node_id: str) -> str:
        node = self.node_map.get(node_id)
        if not node:
            return "custom"
        return _NODE_TYPE_TO_DIFY.get(node.node_type, "custom")
