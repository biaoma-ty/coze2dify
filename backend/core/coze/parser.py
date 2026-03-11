from __future__ import annotations

import json
from typing import Any

import yaml

from core.ir.models import IREdge, IRErrorHandling, IRNode, IRPosition, IRVariable, IRWorkflow
from core.ir.types import ErrorStrategy, IRNodeType, IRVariableType

from .models import CozeBlockInputReference, CozeCanvas, CozeEdge, CozeNode
from .node_parsers import get_node_parser
from .variable_resolver import VariableResolver

# Coze NodeType ID -> IR NodeType
COZE_TYPE_MAP: dict[str, IRNodeType] = {
    "1": IRNodeType.START,
    "2": IRNodeType.END,
    "3": IRNodeType.LLM,
    "4": IRNodeType.PLUGIN,
    "5": IRNodeType.CODE,
    "6": IRNodeType.KNOWLEDGE_RETRIEVAL,
    "8": IRNodeType.CONDITION,
    "9": IRNodeType.SUB_WORKFLOW,
    "12": IRNodeType.DATABASE_CUSTOM_SQL,
    "13": IRNodeType.OUTPUT_EMITTER,
    "15": IRNodeType.TEXT_PROCESSOR,
    "18": IRNodeType.QUESTION_ANSWER,
    "19": IRNodeType.BREAK,
    "20": IRNodeType.VARIABLE_ASSIGNER,
    "21": IRNodeType.LOOP_COUNTED,
    "22": IRNodeType.INTENT_DETECTOR,
    "27": IRNodeType.KNOWLEDGE_WRITE,
    "28": IRNodeType.BATCH,
    "29": IRNodeType.CONTINUE,
    "30": IRNodeType.INPUT_RECEIVER,
    "31": IRNodeType.COMMENT,
    "32": IRNodeType.VARIABLE_AGGREGATOR,
    "37": IRNodeType.MESSAGE_OP,
    "38": IRNodeType.CONVERSATION_OP,
    "39": IRNodeType.CONVERSATION_OP,
    "40": IRNodeType.VARIABLE_ASSIGNER,
    "42": IRNodeType.DATABASE_UPDATE,
    "43": IRNodeType.DATABASE_QUERY,
    "44": IRNodeType.DATABASE_DELETE,
    "45": IRNodeType.HTTP_REQUEST,
    "46": IRNodeType.DATABASE_INSERT,
    "51": IRNodeType.CONVERSATION_OP,
    "52": IRNodeType.CONVERSATION_OP,
    "53": IRNodeType.CONVERSATION_OP,
    "54": IRNodeType.CONVERSATION_OP,
    "55": IRNodeType.MESSAGE_OP,
    "56": IRNodeType.MESSAGE_OP,
    "57": IRNodeType.MESSAGE_OP,
    "58": IRNodeType.JSON_SERIALIZE,
    "59": IRNodeType.JSON_DESERIALIZE,
    "60": IRNodeType.KNOWLEDGE_DELETE,
}

COZE_TYPE_NAMES: dict[str, str] = {
    "1": "Entry",
    "2": "Exit",
    "3": "LLM",
    "4": "Plugin",
    "5": "CodeRunner",
    "6": "KnowledgeRetriever",
    "8": "Selector",
    "9": "SubWorkflow",
    "12": "DatabaseCustomSQL",
    "13": "OutputEmitter",
    "15": "TextProcessor",
    "18": "QuestionAnswer",
    "19": "Break",
    "20": "VariableAssignerInLoop",
    "21": "Loop",
    "22": "IntentDetector",
    "27": "KnowledgeIndexer",
    "28": "Batch",
    "29": "Continue",
    "30": "InputReceiver",
    "31": "Comment",
    "32": "VariableAggregator",
    "37": "MessageList",
    "38": "ClearConversationHistory",
    "39": "CreateConversation",
    "40": "VariableAssigner",
    "42": "DatabaseUpdate",
    "43": "DatabaseQuery",
    "44": "DatabaseDelete",
    "45": "HTTPRequester",
    "46": "DatabaseInsert",
    "51": "ConversationUpdate",
    "52": "ConversationDelete",
    "53": "ConversationList",
    "54": "ConversationHistory",
    "55": "CreateMessage",
    "56": "EditMessage",
    "57": "DeleteMessage",
    "58": "JsonSerialization",
    "59": "JsonDeserialization",
    "60": "KnowledgeDeleter",
}

_VAR_TYPE_MAP = {
    "string": IRVariableType.STRING,
    "integer": IRVariableType.INTEGER,
    "float": IRVariableType.FLOAT,
    "number": IRVariableType.NUMBER,
    "boolean": IRVariableType.BOOLEAN,
    "object": IRVariableType.OBJECT,
    "list": IRVariableType.ARRAY,
    "array": IRVariableType.ARRAY,
}

# Force import node parsers so they register themselves
from core.coze.node_parsers import code as _code_parser  # noqa: F401, E402
from core.coze.node_parsers import http_request as _http_request_parser  # noqa: F401, E402
from core.coze.node_parsers import llm as _llm_parser  # noqa: F401, E402
from core.coze.node_parsers import loop as _loop_parser  # noqa: F401, E402
from core.coze.node_parsers import selector as _selector_parser  # noqa: F401, E402


class CozeParser:
    """Parses Coze canvas JSON/YAML into IR workflow."""

    def __init__(self) -> None:
        self.variable_resolver = VariableResolver()

    def parse_file(self, content: str | bytes, fmt: str = "json") -> IRWorkflow:
        if fmt in ("yaml", "yml"):
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        return self.parse_dict(data)

    def parse_dict(self, data: dict[str, Any]) -> IRWorkflow:
        canvas = CozeCanvas.model_validate(data)
        return self._parse_canvas(canvas)

    def _parse_canvas(self, canvas: CozeCanvas) -> IRWorkflow:
        nodes = [self._parse_node(n) for n in canvas.nodes]

        # Top-level edges live on the canvas and on regular nodes. Composite-node
        # internal edges are handled on the node itself to avoid duplication.
        edges: list[IREdge] = []
        edges.extend(self._collect_edges(canvas.edges))
        for coze_node in canvas.nodes:
            if not coze_node.blocks:
                edges.extend(self._collect_edges(coze_node.edges))

        return IRWorkflow(nodes=nodes, edges=self._dedupe_edges(edges))

    def _parse_node(self, coze_node: CozeNode) -> IRNode:
        node_type = COZE_TYPE_MAP.get(coze_node.type, IRNodeType.UNKNOWN)
        type_name = COZE_TYPE_NAMES.get(coze_node.type, f"Unknown({coze_node.type})")

        position = IRPosition()
        if coze_node.meta and coze_node.meta.position:
            position = IRPosition(
                x=coze_node.meta.position.get("x", 0),
                y=coze_node.meta.position.get("y", 0),
            )

        inputs, outputs, config = self._parse_node_data(coze_node)
        error_handling = self._parse_error_handling(coze_node)
        children = [self._parse_node(block) for block in coze_node.blocks]
        child_edges: list[IREdge] = []
        if coze_node.blocks:
            child_edges.extend(self._collect_edges(coze_node.edges))
            for block in coze_node.blocks:
                child_edges.extend(self._collect_edges(block.edges))
        child_edges = self._dedupe_edges(child_edges)

        # Delegate to type-specific parser
        node_parser = get_node_parser(node_type)
        branches = []
        if node_parser:
            parsed = node_parser.parse(coze_node, self.variable_resolver)
            inputs = parsed.get("inputs", inputs)
            outputs = parsed.get("outputs", outputs)
            config = parsed.get("config", config)
            branches = parsed.get("branches", [])
            if "node_type" in parsed:
                node_type = parsed["node_type"]

        return IRNode(
            id=coze_node.id,
            node_type=node_type,
            title=type_name,
            position=position,
            inputs=inputs,
            outputs=outputs,
            config=config,
            error_handling=error_handling,
            children=children,
            child_edges=child_edges,
            branches=branches,
            source_type_id=coze_node.type,
            source_type_name=type_name,
        )

    def _parse_node_data(self, node: CozeNode) -> tuple[list[IRVariable], list[IRVariable], dict[str, Any]]:
        inputs: list[IRVariable] = []
        outputs: list[IRVariable] = []
        config: dict[str, Any] = {}

        if not node.data:
            return inputs, outputs, config

        coze_inputs = node.data.get("inputs", {})

        for param_data in coze_inputs.get("inputParameters", []):
            name = param_data.get("name", "")
            input_data = param_data.get("input", {})
            var_type = _VAR_TYPE_MAP.get(input_data.get("type", "string"), IRVariableType.ANY)
            var = IRVariable(name=name, var_type=var_type)

            value_data = input_data.get("value", {})
            if value_data:
                if value_data.get("type") == "literal":
                    var.literal_value = value_data.get("content")
                elif value_data.get("type") in ("ref", "object_ref") and isinstance(value_data.get("content"), dict):
                    ref = CozeBlockInputReference.model_validate(value_data["content"])
                    var.ref = self.variable_resolver.resolve_reference(ref)
            inputs.append(var)

        for param_data in coze_inputs.get("outputParameters", []):
            name = param_data.get("name", "")
            input_data = param_data.get("input", {})
            var_type = _VAR_TYPE_MAP.get(input_data.get("type", "string"), IRVariableType.ANY)
            outputs.append(IRVariable(name=name, var_type=var_type))

        return inputs, outputs, config

    def _parse_error_handling(self, node: CozeNode) -> IRErrorHandling:
        if not node.data:
            return IRErrorHandling()

        setting = node.data.get("inputs", {}).get("settingOnError")
        if not setting or not setting.get("switch", False):
            return IRErrorHandling()

        process_type = setting.get("processType", 1)
        strategy_map = {1: ErrorStrategy.THROW, 2: ErrorStrategy.DEFAULT_VALUE, 3: ErrorStrategy.FAIL_BRANCH}

        return IRErrorHandling(
            enabled=True,
            strategy=strategy_map.get(process_type, ErrorStrategy.THROW),
            default_value=setting.get("dataOnErr", ""),
            retry_times=setting.get("retryTimes", 0),
            timeout_ms=setting.get("timeoutMs", 0),
        )

    @staticmethod
    def _collect_edges(coze_edges: list[CozeEdge]) -> list[IREdge]:
        return [
            IREdge(
                source_node_id=e.sourceNodeID,
                target_node_id=e.targetNodeID,
                source_port=e.sourcePortID,
                target_port=e.targetPortID,
            )
            for e in coze_edges
        ]

    @staticmethod
    def _dedupe_edges(edges: list[IREdge]) -> list[IREdge]:
        seen: set[tuple[str, str, str, str]] = set()
        unique: list[IREdge] = []
        for edge in edges:
            key = (edge.source_node_id, edge.target_node_id, edge.source_port, edge.target_port)
            if key in seen:
                continue
            seen.add(key)
            unique.append(edge)
        return unique
