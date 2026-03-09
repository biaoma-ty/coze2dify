from __future__ import annotations

from typing import Any

import yaml

from core.ir.models import IRNode, IRWorkflow
from core.ir.types import IRNodeType

from .edge_builder import EdgeBuilder
from .models import DifyDSL, DifyEdge, DifyGraph, DifyNode, DifyNodeData, DifyWorkflow
from .node_generators import get_node_generator
from .variable_transformer import VariableTransformer

_IR_TO_DIFY_TYPE: dict[IRNodeType, str] = {
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
    IRNodeType.KNOWLEDGE_WRITE: "knowledge-index",
    IRNodeType.PLUGIN: "tool",
    IRNodeType.SUB_WORKFLOW: "tool",
    IRNodeType.VARIABLE_AGGREGATOR: "variable-aggregator",
    IRNodeType.VARIABLE_ASSIGNER: "assigner",
    IRNodeType.TEXT_PROCESSOR: "template-transform",
    IRNodeType.OUTPUT_EMITTER: "answer",
    IRNodeType.INTENT_DETECTOR: "question-classifier",
    IRNodeType.QUESTION_ANSWER: "human-input",
    IRNodeType.INPUT_RECEIVER: "human-input",
    IRNodeType.JSON_SERIALIZE: "code",
    IRNodeType.JSON_DESERIALIZE: "code",
    IRNodeType.CONVERSATION_OP: "http-request",
    IRNodeType.MESSAGE_OP: "http-request",
    IRNodeType.DATABASE_QUERY: "code",
    IRNodeType.DATABASE_INSERT: "code",
    IRNodeType.DATABASE_UPDATE: "code",
    IRNodeType.DATABASE_DELETE: "code",
    IRNodeType.DATABASE_CUSTOM_SQL: "code",
    IRNodeType.KNOWLEDGE_DELETE: "http-request",
}

# Force import node generators so they register themselves
import core.dify.node_generators.llm as _  # noqa: F401, E402
import core.dify.node_generators.code as _  # noqa: F401, E402
import core.dify.node_generators.http_request as _  # noqa: F401, E402
import core.dify.node_generators.if_else as _  # noqa: F401, E402


class DifyGenerator:
    """Generates Dify DSL YAML from IR workflow."""

    def __init__(self) -> None:
        self.var_transformer = VariableTransformer()

    def generate(self, ir_workflow: IRWorkflow) -> DifyDSL:
        flat_nodes = self._flatten_nodes(ir_workflow.nodes)
        node_map = {n.id: n for n in flat_nodes}
        edge_builder = EdgeBuilder(node_map)

        dify_nodes = [
            self._generate_node(ir_node)
            for ir_node in flat_nodes
            if ir_node.node_type != IRNodeType.COMMENT
        ]

        all_edges: list[DifyEdge] = []
        for ir_node in ir_workflow.nodes:
            all_edges.extend(self._build_child_edges(ir_node, edge_builder))

        # Build top-level edges
        all_edges.extend(edge_builder.build_edges(ir_workflow.edges))

        graph = DifyGraph(nodes=dify_nodes, edges=all_edges)
        workflow = DifyWorkflow(graph=graph)

        return DifyDSL(
            app={
                "mode": ir_workflow.mode,
                "name": ir_workflow.name or "Migrated Workflow",
                "description": ir_workflow.description or "Migrated from Coze",
                "icon": "🤖",
                "icon_background": "#FFEAD5",
            },
            workflow=workflow,
        )

    def _generate_node(self, ir_node: IRNode) -> DifyNode:
        dify_type = _IR_TO_DIFY_TYPE.get(ir_node.node_type, "code")

        node_data = DifyNodeData(type=dify_type, title=ir_node.title, desc=ir_node.description)

        # Delegate to type-specific generator
        generator = get_node_generator(ir_node.node_type)
        if generator:
            extra = generator.generate(ir_node, self.var_transformer)
            node_data.extra = extra

        return DifyNode(
            id=ir_node.id,
            data=node_data,
            position={"x": ir_node.position.x, "y": ir_node.position.y},
        )

    def to_yaml(self, dsl: DifyDSL) -> str:
        return yaml.dump(dsl.model_dump(exclude_none=True), default_flow_style=False, allow_unicode=True, sort_keys=False)

    def to_dict(self, dsl: DifyDSL) -> dict[str, Any]:
        return dsl.model_dump(exclude_none=True)

    def _flatten_nodes(self, nodes: list[IRNode]) -> list[IRNode]:
        flattened: list[IRNode] = []
        for node in nodes:
            flattened.append(node)
            if node.children:
                flattened.extend(self._flatten_nodes(node.children))
        return flattened

    def _build_child_edges(
        self,
        ir_node: IRNode,
        edge_builder: EdgeBuilder,
        in_loop: bool = False,
        in_iteration: bool = False,
    ) -> list[DifyEdge]:
        node_in_loop = in_loop or ir_node.node_type in (IRNodeType.LOOP_COUNTED, IRNodeType.LOOP_INFINITE)
        node_in_iteration = in_iteration or ir_node.node_type in (IRNodeType.LOOP_ARRAY, IRNodeType.BATCH)

        edges: list[DifyEdge] = []
        if ir_node.child_edges:
            edges.extend(
                edge_builder.build_edges(
                    ir_node.child_edges,
                    in_loop=node_in_loop,
                    in_iteration=node_in_iteration,
                )
            )

        for child in ir_node.children:
            edges.extend(self._build_child_edges(child, edge_builder, node_in_loop, node_in_iteration))

        return edges
