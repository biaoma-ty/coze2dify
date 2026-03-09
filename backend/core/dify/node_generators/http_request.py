from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType

from . import register_generator


class HTTPRequestNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        config = ir_node.config
        return {
            "method": config.get("method", "GET"),
            "url": config.get("url", ""),
            "headers": config.get("headers", ""),
            "body": {"type": config.get("body_type", "none"), "data": config.get("body", "")},
            "authorization": config.get("authorization", {"type": "no-auth"}),
        }


register_generator(IRNodeType.HTTP_REQUEST, HTTPRequestNodeGenerator())
