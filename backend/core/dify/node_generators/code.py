from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType, IRVariableType

from . import register_generator

_TYPE_MAP = {
    IRVariableType.STRING: "string",
    IRVariableType.INTEGER: "number",
    IRVariableType.FLOAT: "number",
    IRVariableType.NUMBER: "number",
    IRVariableType.BOOLEAN: "boolean",
    IRVariableType.OBJECT: "object",
    IRVariableType.ARRAY: "array[any]",
    IRVariableType.ANY: "string",
}


class CodeNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        config = ir_node.config
        language = config.get("language", "python3")

        extra: dict[str, Any] = {
            "code_language": language,
            "code": config.get("code", ""),
            "variables": [],
            "outputs": {},
        }

        # Map input variables
        for inp in ir_node.inputs:
            var_entry: dict[str, Any] = {
                "variable": inp.name,
                "value_selector": [],
            }
            if inp.ref:
                var_entry["value_selector"] = var_transformer.to_selector(inp.ref)
            extra["variables"].append(var_entry)

        # Map output variables
        for out in ir_node.outputs:
            extra["outputs"][out.name] = {"type": _TYPE_MAP.get(out.var_type, "string")}

        return extra


register_generator(IRNodeType.CODE, CodeNodeGenerator())
