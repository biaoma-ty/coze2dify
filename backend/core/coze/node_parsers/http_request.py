from __future__ import annotations

from typing import Any

from core.ir.models import IRVariable
from core.ir.types import IRNodeType, IRVariableType

from . import register_parser


class HTTPRequestNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        config: dict[str, Any] = {}
        outputs: list[IRVariable] = []

        data = node.data or {}
        http_config = data.get("inputs", {}).get("httpRequestNode", {})

        if http_config:
            config["method"] = http_config.get("method", "GET")
            config["url"] = http_config.get("url", "")
            config["headers"] = http_config.get("headers", {})
            config["body"] = http_config.get("body", "")
            config["body_type"] = http_config.get("bodyType", "none")
            config["authorization"] = http_config.get("authorization", {})

        outputs.append(IRVariable(name="body", var_type=IRVariableType.STRING))
        outputs.append(IRVariable(name="status_code", var_type=IRVariableType.INTEGER))
        outputs.append(IRVariable(name="headers", var_type=IRVariableType.OBJECT))

        return {"outputs": outputs, "config": config}


register_parser(IRNodeType.HTTP_REQUEST, HTTPRequestNodeParser())
