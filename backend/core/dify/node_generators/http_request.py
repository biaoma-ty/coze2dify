from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType

from . import register_generator


class HTTPRequestNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        config = ir_node.config
        variables: list[dict[str, Any]] = []
        for inp in ir_node.inputs:
            var_entry = {"variable": inp.name, "value_selector": []}
            if inp.ref:
                var_entry["value_selector"] = var_transformer.to_selector(inp.ref)
            variables.append(var_entry)

        # Convert headers dict to Dify's newline-separated string format
        raw_headers = config.get("headers", "")
        if isinstance(raw_headers, dict):
            raw_headers = "\n".join(f"{k}: {v}" for k, v in raw_headers.items())

        return {
            "variables": variables,
            "method": str(config.get("method", "get")).lower(),
            "url": config.get("url", ""),
            "headers": raw_headers,
            "params": config.get("params", ""),
            "body": {"type": config.get("body_type", "none"), "data": config.get("body", "")},
            "authorization": config.get("authorization", {"type": "no-auth"}),
            "timeout": config.get(
                "timeout",
                {
                    "max_connect_timeout": 0,
                    "max_read_timeout": 0,
                    "max_write_timeout": 0,
                },
            ),
            "ssl_verify": config.get("ssl_verify", True),
            "retry_config": config.get(
                "retry_config",
                {
                    "retry_enabled": True,
                    "max_retries": 3,
                    "retry_interval": 100,
                },
            ),
        }


register_generator(IRNodeType.HTTP_REQUEST, HTTPRequestNodeGenerator())
