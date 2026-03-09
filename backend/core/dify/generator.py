from __future__ import annotations

from typing import Any

import yaml

from core.ir.models import IREdge, IRNode, IRVariable, IRWorkflow
from core.ir.types import IRNodeType, IRVariableType

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

_IR_TO_INPUT_TYPE: dict[IRVariableType, str] = {
    IRVariableType.STRING: "text-input",
    IRVariableType.INTEGER: "number",
    IRVariableType.FLOAT: "number",
    IRVariableType.NUMBER: "number",
    IRVariableType.BOOLEAN: "checkbox",
    IRVariableType.OBJECT: "json_object",
    IRVariableType.ARRAY: "json",
    IRVariableType.ARRAY_STRING: "json",
    IRVariableType.ARRAY_NUMBER: "json",
    IRVariableType.ARRAY_OBJECT: "json",
    IRVariableType.FILE: "file",
    IRVariableType.ANY: "text-input",
}

_ITERATION_NODE_Z_INDEX = 1
_COMPOSITE_CHILD_Z_INDEX = 1002

# Force import node generators so they register themselves
from core.dify.node_generators import code as _code_generator  # noqa: F401, E402
from core.dify.node_generators import http_request as _http_request_generator  # noqa: F401, E402
from core.dify.node_generators import if_else as _if_else_generator  # noqa: F401, E402
from core.dify.node_generators import llm as _llm_generator  # noqa: F401, E402


class DifyGenerator:
    """Generates Dify DSL YAML from IR workflow."""

    def __init__(self) -> None:
        self.var_transformer = VariableTransformer()

    def generate(self, ir_workflow: IRWorkflow) -> DifyDSL:
        flat_nodes = self._flatten_nodes(ir_workflow.nodes)
        node_map = {n.id: n for n in flat_nodes}
        edge_builder = EdgeBuilder(node_map)

        dify_nodes: list[DifyNode] = []
        for ir_node in ir_workflow.nodes:
            dify_nodes.extend(self._generate_nodes(ir_node))

        all_edges = edge_builder.build_edges(ir_workflow.edges)
        for ir_node in ir_workflow.nodes:
            all_edges.extend(self._build_composite_edges(ir_node, edge_builder))

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

    def _generate_nodes(self, ir_node: IRNode, parent: IRNode | None = None) -> list[DifyNode]:
        nodes: list[DifyNode] = []
        if ir_node.node_type != IRNodeType.COMMENT:
            nodes.append(self._generate_node(ir_node, parent))

        if self._is_composite_node(ir_node):
            nodes.append(self._generate_composite_start_node(ir_node))

        for child in ir_node.children:
            next_parent = ir_node if self._is_composite_node(ir_node) else parent
            nodes.extend(self._generate_nodes(child, next_parent))

        return nodes

    def _generate_node(self, ir_node: IRNode, parent: IRNode | None = None) -> DifyNode:
        dify_type = _IR_TO_DIFY_TYPE.get(ir_node.node_type, "code")
        node_payload = self._default_node_payload(ir_node)

        # Delegate to type-specific generator
        generator = get_node_generator(ir_node.node_type)
        if generator:
            node_payload.update(generator.generate(ir_node, self.var_transformer))

        node_kwargs: dict[str, Any] = {
            "id": ir_node.id,
            "position": {"x": ir_node.position.x, "y": ir_node.position.y},
        }

        if self._is_iteration_node(ir_node):
            node_kwargs["width"] = 388
            node_kwargs["height"] = 178
            node_kwargs["zIndex"] = _ITERATION_NODE_Z_INDEX
        elif self._is_loop_node(ir_node):
            node_kwargs["width"] = 884
            node_kwargs["height"] = 225
            node_kwargs["zIndex"] = _ITERATION_NODE_Z_INDEX

        if parent:
            node_kwargs["parentId"] = parent.id
            node_kwargs["zIndex"] = _COMPOSITE_CHILD_Z_INDEX
            self._annotate_child_payload(node_payload, parent)

        node_data = DifyNodeData(
            type=dify_type,
            title=ir_node.title,
            desc=ir_node.description,
            **node_payload,
        )

        return DifyNode(data=node_data, **node_kwargs)

    def to_yaml(self, dsl: DifyDSL) -> str:
        return yaml.dump(
            dsl.model_dump(exclude_none=True), default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    def to_dict(self, dsl: DifyDSL) -> dict[str, Any]:
        return dsl.model_dump(exclude_none=True)

    def _flatten_nodes(self, nodes: list[IRNode]) -> list[IRNode]:
        flattened: list[IRNode] = []
        for node in nodes:
            flattened.append(node)
            if node.children:
                flattened.extend(self._flatten_nodes(node.children))
        return flattened

    def _build_composite_edges(self, ir_node: IRNode, edge_builder: EdgeBuilder) -> list[DifyEdge]:
        edges: list[DifyEdge] = []
        if self._is_composite_node(ir_node):
            for child_edge in ir_node.child_edges:
                mapped_edges = self._map_composite_edge(ir_node, child_edge, edge_builder)
                edges.extend(mapped_edges)

        for child in ir_node.children:
            edges.extend(self._build_composite_edges(child, edge_builder))

        return edges

    def _default_node_payload(self, ir_node: IRNode) -> dict[str, Any]:
        match ir_node.node_type:
            case IRNodeType.START:
                return {"variables": [self._to_start_variable(var) for var in ir_node.inputs]}
            case IRNodeType.END:
                return {"outputs": self._to_end_outputs(ir_node.inputs)}
            case IRNodeType.CODE:
                return {"code": "", "code_language": "python3", "variables": [], "outputs": {}}
            case IRNodeType.HTTP_REQUEST:
                return {
                    "variables": [],
                    "method": "get",
                    "url": "",
                    "headers": "",
                    "params": "",
                    "body": {"type": "none", "data": []},
                    "authorization": {"type": "no-auth", "config": None},
                    "timeout": {
                        "max_connect_timeout": 0,
                        "max_read_timeout": 0,
                        "max_write_timeout": 0,
                    },
                    "ssl_verify": True,
                    "retry_config": {
                        "retry_enabled": True,
                        "max_retries": 3,
                        "retry_interval": 100,
                    },
                }
            case IRNodeType.CONDITION:
                return {
                    "cases": [{"case_id": "true", "logical_operator": "and", "conditions": []}],
                    "isInIteration": False,
                    "isInLoop": False,
                }
            case IRNodeType.LOOP_COUNTED | IRNodeType.LOOP_INFINITE:
                return {
                    "start_node_id": self._get_composite_start_node_id(ir_node),
                    "logical_operator": "and",
                    "break_conditions": [],
                    "loop_count": int(ir_node.config.get("loop_count") or ir_node.config.get("max_iterations") or 10),
                    "error_handle_mode": "terminated",
                    "loop_variables": [],
                }
            case IRNodeType.LOOP_ARRAY | IRNodeType.BATCH:
                iterator_selector = ir_node.config.get("iterator_selector", [])
                if not isinstance(iterator_selector, list):
                    iterator_selector = []
                return {
                    "start_node_id": self._get_composite_start_node_id(ir_node),
                    "iterator_selector": iterator_selector,
                    "iterator_input_type": "array",
                    "output_selector": self._get_composite_output_selector(ir_node),
                    "output_type": self._get_iteration_output_type(ir_node),
                    "is_parallel": ir_node.node_type == IRNodeType.BATCH,
                    "parallel_nums": 10,
                    "error_handle_mode": "terminated",
                    "flatten_output": True,
                    "_isShowTips": False,
                }
            case IRNodeType.TEXT_PROCESSOR:
                return {
                    "variables": self._to_value_variables(ir_node.inputs),
                    "template": ir_node.config.get("template", ""),
                }
            case IRNodeType.OUTPUT_EMITTER:
                return {
                    "variables": self._to_value_variables(ir_node.inputs),
                    "answer": self._build_text_template(ir_node.inputs),
                }
            case _:
                return {}

    def _to_start_variable(self, var: IRVariable) -> dict[str, Any]:
        item: dict[str, Any] = {
            "type": _IR_TO_INPUT_TYPE.get(var.var_type, "text-input"),
            "label": var.name,
            "variable": var.name,
            "required": var.required,
        }
        if var.description:
            item["hint"] = var.description
        if var.default_value is not None:
            item["default"] = var.default_value
        return item

    def _to_value_variables(self, variables: list[IRVariable]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for var in variables:
            entry = {"variable": var.name, "value_selector": []}
            if var.ref:
                entry["value_selector"] = self.var_transformer.to_selector(var.ref)
            result.append(entry)
        return result

    def _to_end_outputs(self, variables: list[IRVariable]) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        for var in variables:
            entry: dict[str, Any] = {"variable": var.name, "value_selector": []}
            if var.ref:
                entry["value_selector"] = self.var_transformer.to_selector(var.ref)
            outputs.append(entry)
        return outputs

    def _build_text_template(self, variables: list[IRVariable]) -> str:
        fragments: list[str] = []
        for var in variables:
            if var.literal_value is not None:
                fragments.append(str(var.literal_value))
            elif var.ref:
                fragments.append(self.var_transformer.to_template(var.ref))
        return "\n".join(fragment for fragment in fragments if fragment)

    @staticmethod
    def _get_composite_start_node_id(ir_node: IRNode) -> str:
        return f"{ir_node.id}start"

    def _generate_composite_start_node(self, ir_node: IRNode) -> DifyNode:
        is_iteration = self._is_iteration_node(ir_node)
        return DifyNode(
            id=self._get_composite_start_node_id(ir_node),
            type="custom-iteration-start" if is_iteration else "custom-loop-start",
            data=DifyNodeData(
                type="iteration-start" if is_iteration else "loop-start",
                title="",
                desc="",
                isInIteration=is_iteration,
                isInLoop=not is_iteration,
            ),
            parentId=ir_node.id,
            position={"x": 24 if is_iteration else 60, "y": 68 if is_iteration else 88.5},
            width=44,
            height=48,
            zIndex=_COMPOSITE_CHILD_Z_INDEX,
            draggable=False,
            selectable=False,
        )

    def _map_composite_edge(self, parent: IRNode, edge: IREdge, edge_builder: EdgeBuilder) -> list[DifyEdge]:
        if edge.source_node_id == parent.id:
            target_node = self._find_node(parent, edge.target_node_id)
            return [
                self._make_special_edge(
                    source_id=self._get_composite_start_node_id(parent),
                    target_id=edge.target_node_id,
                    source_type="iteration-start" if self._is_iteration_node(parent) else "loop-start",
                    target_type=_IR_TO_DIFY_TYPE.get(target_node.node_type, "custom") if target_node else "custom",
                    parent=parent,
                )
            ]

        if edge.target_node_id == parent.id:
            return []

        mapped_edges = edge_builder.build_edges(
            [edge],
            in_loop=self._is_loop_node(parent),
            in_iteration=self._is_iteration_node(parent),
        )
        for mapped_edge in mapped_edges:
            self._annotate_edge_for_parent(mapped_edge, parent)
        return mapped_edges

    def _make_special_edge(
        self,
        *,
        source_id: str,
        target_id: str,
        source_type: str,
        target_type: str,
        parent: IRNode,
        source_handle: str = "source",
        target_handle: str = "target",
    ) -> DifyEdge:
        data: dict[str, Any] = {
            "sourceType": source_type,
            "targetType": target_type,
            "isInIteration": self._is_iteration_node(parent),
            "isInLoop": self._is_loop_node(parent),
        }
        if self._is_iteration_node(parent):
            data["iteration_id"] = parent.id
        if self._is_loop_node(parent):
            data["loop_id"] = parent.id

        return DifyEdge(
            id=f"{source_id}-{source_handle}-{target_id}-{target_handle}",
            source=source_id,
            sourceHandle=source_handle,
            target=target_id,
            targetHandle=target_handle,
            data=data,
            zIndex=_COMPOSITE_CHILD_Z_INDEX,
        )

    def _annotate_child_payload(self, node_payload: dict[str, Any], parent: IRNode) -> None:
        is_iteration = self._is_iteration_node(parent)
        node_payload["isInIteration"] = is_iteration
        node_payload["isInLoop"] = not is_iteration
        if is_iteration:
            node_payload["iteration_id"] = parent.id
        else:
            node_payload["loop_id"] = parent.id

    def _annotate_edge_for_parent(self, edge: DifyEdge, parent: IRNode) -> None:
        edge.zIndex = _COMPOSITE_CHILD_Z_INDEX
        edge.data["isInIteration"] = self._is_iteration_node(parent)
        edge.data["isInLoop"] = self._is_loop_node(parent)
        if self._is_iteration_node(parent):
            edge.data["iteration_id"] = parent.id
        if self._is_loop_node(parent):
            edge.data["loop_id"] = parent.id

    def _get_composite_output_selector(self, ir_node: IRNode) -> list[str]:
        for edge in reversed(ir_node.child_edges):
            if edge.target_node_id != ir_node.id:
                continue
            source_node = self._find_node(ir_node, edge.source_node_id)
            if source_node and source_node.outputs:
                return [source_node.id, source_node.outputs[0].name]
        return []

    def _get_iteration_output_type(self, ir_node: IRNode) -> str:
        selector = self._get_composite_output_selector(ir_node)
        if len(selector) != 2:
            return "array"
        source_node = self._find_node(ir_node, selector[0])
        if not source_node:
            return "array"
        for output in source_node.outputs:
            if output.name == selector[1]:
                return self._wrap_iteration_output_type(output.var_type)
        return "array"

    def _find_node(self, root: IRNode, node_id: str) -> IRNode | None:
        for child in root.children:
            if child.id == node_id:
                return child
            found = self._find_node(child, node_id)
            if found:
                return found
        return None

    def _wrap_iteration_output_type(self, var_type: IRVariableType) -> str:
        match var_type:
            case IRVariableType.STRING:
                return "array[string]"
            case IRVariableType.INTEGER | IRVariableType.FLOAT | IRVariableType.NUMBER:
                return "array[number]"
            case IRVariableType.BOOLEAN:
                return "array[boolean]"
            case IRVariableType.OBJECT:
                return "array[object]"
            case IRVariableType.FILE:
                return "array[file]"
            case IRVariableType.ARRAY:
                return "array"
            case IRVariableType.ARRAY_STRING:
                return "array[string]"
            case IRVariableType.ARRAY_NUMBER:
                return "array[number]"
            case IRVariableType.ARRAY_OBJECT:
                return "array[object]"
            case _:
                return "array"

    @staticmethod
    def _is_composite_node(ir_node: IRNode) -> bool:
        return ir_node.node_type in (
            IRNodeType.LOOP_ARRAY,
            IRNodeType.BATCH,
            IRNodeType.LOOP_COUNTED,
            IRNodeType.LOOP_INFINITE,
        )

    @staticmethod
    def _is_iteration_node(ir_node: IRNode) -> bool:
        return ir_node.node_type in (IRNodeType.LOOP_ARRAY, IRNodeType.BATCH)

    @staticmethod
    def _is_loop_node(ir_node: IRNode) -> bool:
        return ir_node.node_type in (IRNodeType.LOOP_COUNTED, IRNodeType.LOOP_INFINITE)
