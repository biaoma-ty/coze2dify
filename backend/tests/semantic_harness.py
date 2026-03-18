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
    scopes = _build_ir_scopes(workflow, inputs)

    for node_id in order:
        node = node_map[node_id]
        if node.node_type == IRNodeType.START:
            values[node.id] = dict(inputs)
        elif node.node_type == IRNodeType.CODE:
            arguments = {var.name: _resolve_ir_variable(values, var, scopes) for var in node.inputs}
            values[node.id] = _execute_python_code(node.config.get("code", ""), arguments)
            terminal = values[node.id]
        elif node.node_type == IRNodeType.LLM:
            values[node.id] = _trace_ir_llm_node(node, values, scopes)
            terminal = values[node.id]
        elif node.node_type == IRNodeType.OUTPUT_EMITTER:
            values[node.id] = {"answer": _build_ir_answer(node.inputs, values, scopes)}
            terminal = values[node.id]
        elif node.node_type == IRNodeType.END:
            values[node.id] = {var.name: _resolve_ir_variable(values, var, scopes) for var in node.inputs}
            terminal = values[node.id]
        else:
            values[node.id] = {}

    return terminal


def execute_dify_workflow(dsl: DifyDSL, inputs: dict[str, Any]) -> dict[str, Any]:
    node_map = {node.id: node for node in dsl.workflow.graph.nodes}
    order = _topological_order(node_map, [(edge.source, edge.target) for edge in dsl.workflow.graph.edges])
    values: dict[str, dict[str, Any]] = {}
    terminal: dict[str, Any] = {}
    scopes = _build_dify_scopes(dsl, inputs)

    for node_id in order:
        node = node_map[node_id]
        node_type = node.data.type
        if node_type == "start":
            values[node.id] = dict(inputs)
        elif node_type == "code":
            arguments = {
                entry["variable"]: _resolve_selector(values, entry.get("value_selector", []), scopes)
                for entry in node.data.variables
            }
            values[node.id] = _execute_python_code(node.data.code, arguments)
            terminal = values[node.id]
        elif node_type == "llm":
            values[node.id] = _trace_dify_llm_node(node.data, values, scopes)
            terminal = values[node.id]
        elif node_type == "answer":
            values[node.id] = {"answer": _render_template(node.data.answer, values, scopes)}
            terminal = values[node.id]
        elif node_type == "end":
            values[node.id] = {
                entry["variable"]: _resolve_selector(values, entry.get("value_selector", []), scopes)
                for entry in node.data.outputs
            }
            terminal = values[node.id]
        else:
            values[node.id] = {}

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


def _resolve_ir_variable(values: dict[str, dict[str, Any]], var: IRVariable, scopes: dict[str, dict[str, Any]]) -> Any:
    if var.literal_value is not None:
        return var.literal_value
    if var.ref is None:
        return None
    if var.ref.source_type == "global_app":
        return _resolve_scoped_value(scopes.get("env", {}), var.ref.field_name, var.ref.nested_path)
    if var.ref.source_type == "global_user":
        return _resolve_scoped_value(scopes.get("conversation", {}), var.ref.field_name, var.ref.nested_path)
    if var.ref.source_type == "global_system":
        return _resolve_scoped_value(scopes.get("sys", {}), var.ref.field_name, var.ref.nested_path)
    return _resolve_scoped_value(values.get(var.ref.source_node_id, {}), var.ref.field_name, var.ref.nested_path)


def _resolve_selector(
    values: dict[str, dict[str, Any]],
    selector: list[str],
    scopes: dict[str, dict[str, Any]] | None = None,
) -> Any:
    if len(selector) < 2:
        return None
    scopes = scopes or {}
    scope_root = scopes.get(selector[0])
    if scope_root is not None:
        current: Any = scope_root.get(selector[1])
    else:
        current = values.get(selector[0], {}).get(selector[1])
    for part in selector[2:]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _build_ir_answer(
    variables: list[IRVariable],
    values: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
) -> str:
    fragments: list[str] = []
    for var in variables:
        if var.literal_value is not None:
            fragments.append(str(var.literal_value))
        elif var.ref is not None:
            resolved = _resolve_ir_variable(values, var, scopes)
            if resolved is not None:
                fragments.append(str(resolved))
    return "\n".join(fragment for fragment in fragments if fragment)


def _render_template(
    template: str,
    values: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]] | None = None,
) -> str:
    def replace(match: re.Match[str]) -> str:
        parts = match.group(1).split(".")
        return str(_resolve_selector(values, parts, scopes) or "")

    return _TEMPLATE_RE.sub(replace, template)


def _execute_python_code(code: str, arguments: dict[str, Any]) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    exec(code, {}, namespace)  # noqa: S102 - fixtures are repo-local test inputs
    return dict(namespace["main"](**arguments))


def _build_ir_scopes(workflow: IRWorkflow, inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    env: dict[str, Any] = {}
    conversation: dict[str, Any] = {}
    sys = {"query": _infer_query(inputs)}

    for variable in workflow.global_variables:
        if variable.scope == "global_app":
            env[variable.name] = variable.default_value
        elif variable.scope == "global_user":
            conversation[variable.name] = variable.default_value
        elif variable.scope == "global_system":
            sys[variable.name] = variable.default_value

    return {"env": env, "conversation": conversation, "sys": sys}


def _build_dify_scopes(dsl: DifyDSL, inputs: dict[str, Any]) -> dict[str, dict[str, Any]]:
    env = {
        variable.get("name"): variable.get("value")
        for variable in dsl.workflow.environment_variables
        if isinstance(variable, dict)
    }
    conversation = {
        variable.get("name"): variable.get("value")
        for variable in dsl.workflow.conversation_variables
        if isinstance(variable, dict)
    }
    sys = {"query": _infer_query(inputs)}
    return {"env": env, "conversation": conversation, "sys": sys}


def _trace_ir_llm_node(
    node: Any,
    values: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    context_value: Any = None
    replacements: dict[str, str] = {}

    for inp in node.inputs:
        if not inp.name:
            continue
        if inp.ref is not None:
            resolved = _resolve_ir_variable(values, inp, scopes)
            if inp.name.lower() == "context":
                context_value = resolved
            replacement = "" if resolved is None else str(resolved)
        elif inp.literal_value is not None:
            replacement = str(inp.literal_value)
        else:
            replacement = ""
        replacements["{{" + inp.name + "}}"] = replacement
        replacements["{" + inp.name + "}"] = replacement

    raw_prompts = node.config.get("prompt_messages")
    if isinstance(raw_prompts, list) and raw_prompts:
        prompts = [
            {
                "role": str(entry.get("role") or "user"),
                "text": _replace_placeholders(str(entry.get("text") or ""), replacements),
            }
            for entry in raw_prompts
            if isinstance(entry, dict)
        ]
    else:
        prompt = _replace_placeholders(str(node.config.get("prompt_template") or ""), replacements)
        system_prompt = _replace_placeholders(str(node.config.get("system_prompt") or ""), replacements)
        prompts = []
        if system_prompt:
            prompts.append({"role": "system", "text": system_prompt})
        prompts.append({"role": "user", "text": prompt})

    query_replacements = dict(replacements)
    query_replacements["{{query}}"] = str(scopes.get("sys", {}).get("query", "") or "")
    query_replacements["{query}"] = str(scopes.get("sys", {}).get("query", "") or "")

    return {
        "prompt": prompts,
        "context": context_value,
        "memory": {
            "enabled": bool(node.config.get("enable_chat_history", False)),
            "size": int(node.config.get("chat_history_round", 10) or 10),
            "query_prompt_template": _replace_placeholders(
                str(node.config.get("memory_query_prompt_template", "{{query}}")),
                query_replacements,
            ),
            "role_prefix": dict(node.config.get("memory_role_prefix") or {"assistant": "", "user": ""}),
        },
    }


def _trace_dify_llm_node(
    node_data: Any,
    values: dict[str, dict[str, Any]],
    scopes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    context_config = getattr(node_data, "context", {}) or {}
    context_value = (
        _resolve_selector(values, context_config.get("variable_selector", []), scopes)
        if context_config.get("enabled")
        else None
    )
    prompts = [
        {
            "role": entry.get("role", ""),
            "text": _render_template(
                entry.get("text", "").replace("{{#context#}}", "" if context_value is None else str(context_value)),
                values,
                scopes,
            ),
        }
        for entry in node_data.prompt_template
    ]
    memory_config = getattr(node_data, "memory", {}) or {}
    return {
        "prompt": prompts,
        "context": context_value,
        "memory": {
            "enabled": bool(memory_config.get("window", {}).get("enabled", False)),
            "size": int(memory_config.get("window", {}).get("size", 0) or 0),
            "query_prompt_template": _render_template(
                str(memory_config.get("query_prompt_template", "")),
                values,
                scopes,
            ),
            "role_prefix": dict(memory_config.get("role_prefix") or {"assistant": "", "user": ""}),
        },
    }


def _replace_placeholders(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for placeholder, replacement in replacements.items():
        rendered = rendered.replace(placeholder, replacement)
    return rendered


def _resolve_scoped_value(root: dict[str, Any], field_name: str, nested_path: list[str]) -> Any:
    current: Any = root.get(field_name)
    for part in nested_path:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _infer_query(inputs: dict[str, Any]) -> Any:
    if "query" in inputs:
        return inputs["query"]
    if "input" in inputs:
        return inputs["input"]
    if inputs:
        return next(iter(inputs.values()))
    return ""
