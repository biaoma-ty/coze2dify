from __future__ import annotations

import re
from collections import defaultdict, deque
from typing import Any

from core.dify.models import DifyDSL
from core.ir.models import IRVariable, IRWorkflow
from core.ir.types import IRNodeType

_TEMPLATE_RE = re.compile(r"\{\{#([^#]+)#\}\}")


def execute_ir_workflow(workflow: IRWorkflow, inputs: dict[str, Any]) -> dict[str, Any]:
    node_map = {node.id: node for node in workflow.nodes}
    order = _topological_order(node_map, [(edge.source_node_id, edge.target_node_id) for edge in workflow.edges])
    values: dict[str, dict[str, Any]] = {}
    terminal: dict[str, Any] = {}

    for node_id in order:
        node = node_map[node_id]
        if node.node_type == IRNodeType.START:
            values[node.id] = dict(inputs)
        elif node.node_type == IRNodeType.CODE:
            arguments = {var.name: _resolve_ir_variable(values, var) for var in node.inputs}
            values[node.id] = _execute_python_code(node.config.get("code", ""), arguments)
            terminal = values[node.id]
        elif node.node_type == IRNodeType.OUTPUT_EMITTER:
            answer = _build_ir_answer(node.inputs, values)
            values[node.id] = {"answer": answer}
            terminal = values[node.id]
        elif node.node_type == IRNodeType.END:
            values[node.id] = {var.name: _resolve_ir_variable(values, var) for var in node.inputs}
            terminal = values[node.id]
        else:
            values[node.id] = {}
            terminal = values[node.id]

    return terminal


def execute_dify_workflow(dsl: DifyDSL, inputs: dict[str, Any]) -> dict[str, Any]:
    node_map = {node.id: node for node in dsl.workflow.graph.nodes}
    order = _topological_order(node_map, [(edge.source, edge.target) for edge in dsl.workflow.graph.edges])
    values: dict[str, dict[str, Any]] = {}
    terminal: dict[str, Any] = {}

    for node_id in order:
        node = node_map[node_id]
        node_type = node.data.type
        if node_type == "start":
            values[node.id] = dict(inputs)
        elif node_type == "code":
            arguments = {
                entry["variable"]: _resolve_selector(values, entry.get("value_selector", []))
                for entry in node.data.variables
            }
            values[node.id] = _execute_python_code(node.data.code, arguments)
            terminal = values[node.id]
        elif node_type == "answer":
            values[node.id] = {"answer": _render_template(node.data.answer, values)}
            terminal = values[node.id]
        elif node_type == "end":
            values[node.id] = {
                entry["variable"]: _resolve_selector(values, entry.get("value_selector", []))
                for entry in node.data.outputs
            }
            terminal = values[node.id]
        else:
            values[node.id] = {}
            terminal = values[node.id]

    return terminal


def _topological_order(node_map: dict[str, Any], edges: list[tuple[str, str]]) -> list[str]:
    indegree = {node_id: 0 for node_id in node_map}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        if source not in node_map or target not in node_map:
            continue
        outgoing[source].append(target)
        indegree[target] += 1

    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for target in outgoing[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    return order if len(order) == len(node_map) else list(node_map)


def _resolve_ir_variable(values: dict[str, dict[str, Any]], var: IRVariable) -> Any:
    if var.literal_value is not None:
        return var.literal_value
    if var.ref is None:
        return None
    return values.get(var.ref.source_node_id, {}).get(var.ref.field_name)


def _resolve_selector(values: dict[str, dict[str, Any]], selector: list[str]) -> Any:
    if len(selector) < 2:
        return None
    current: Any = values.get(selector[0], {}).get(selector[1])
    for part in selector[2:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _build_ir_answer(variables: list[IRVariable], values: dict[str, dict[str, Any]]) -> str:
    fragments: list[str] = []
    for var in variables:
        if var.literal_value is not None:
            fragments.append(str(var.literal_value))
        elif var.ref is not None:
            resolved = values.get(var.ref.source_node_id, {}).get(var.ref.field_name)
            if resolved is not None:
                fragments.append(str(resolved))
    return "\n".join(fragment for fragment in fragments if fragment)


def _render_template(template: str, values: dict[str, dict[str, Any]]) -> str:
    def replace(match: re.Match[str]) -> str:
        parts = match.group(1).split(".")
        return str(_resolve_selector(values, parts) or "")

    return _TEMPLATE_RE.sub(replace, template)


def _execute_python_code(code: str, arguments: dict[str, Any]) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(code, {}, namespace)  # noqa: S102 - fixtures are repo-local test inputs
    return dict(namespace["main"](**arguments))
