from __future__ import annotations

from typing import Any

from core.ir.models import IRVariable
from core.ir.types import IRNodeType, IRVariableType

from . import register_parser

_LANGUAGE_MAP = {0: "python3", 1: "python3", 2: "javascript", 3: "javascript"}
_TYPE_MAP = {
    "string": IRVariableType.STRING,
    "integer": IRVariableType.INTEGER,
    "float": IRVariableType.FLOAT,
    "boolean": IRVariableType.BOOLEAN,
    "object": IRVariableType.OBJECT,
    "list": IRVariableType.ARRAY,
}


class CodeNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        config: dict[str, Any] = {}
        outputs: list[IRVariable] = []

        data = node.data or {}
        coze_inputs = data.get("inputs", {})

        # Real Coze exports store code as a plain string and language as a sibling field.
        code_config = coze_inputs.get("code")
        lang_id = coze_inputs.get("language", 1)
        code = ""
        if isinstance(code_config, dict):
            lang_id = code_config.get("language", lang_id)
            code = code_config.get("code", "")
        elif isinstance(code_config, str):
            code = code_config

        if code:
            config["language"] = _LANGUAGE_MAP.get(lang_id, "python3")
            config["code"] = code

        output_params = coze_inputs.get("outputParameters") or data.get("outputs", [])
        for param in output_params:
            name = param.get("name", "")
            input_data = param.get("input", {})
            var_type_str = input_data.get("type") or param.get("type", "string")
            outputs.append(IRVariable(name=name, var_type=_TYPE_MAP.get(var_type_str, IRVariableType.ANY)))

        return {"outputs": outputs, "config": config}


register_parser(IRNodeType.CODE, CodeNodeParser())
