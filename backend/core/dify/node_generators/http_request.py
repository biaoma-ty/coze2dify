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

        timeout = config.get("timeout")
        if not isinstance(timeout, dict):
            timeout = {
                "max_connect_timeout": 0,
                "max_read_timeout": 0,
                "max_write_timeout": 0,
            }
        else:
            timeout = dict(timeout)

        retry_config = config.get("retry_config")
        if not isinstance(retry_config, dict):
            retry_config = {
                "retry_enabled": False,
                "max_retries": 0,
                "retry_interval": 100,
            }
        else:
            retry_config = dict(retry_config)

        error_handling = getattr(ir_node, "error_handling", None)
        if error_handling and getattr(error_handling, "enabled", False):
            timeout_ms = max(int(getattr(error_handling, "timeout_ms", 0) or 0), 0)
            if timeout_ms > 0:
                timeout["max_connect_timeout"] = timeout_ms
                timeout["max_read_timeout"] = timeout_ms
                timeout["max_write_timeout"] = timeout_ms

            retry_times = max(int(getattr(error_handling, "retry_times", 0) or 0), 0)
            retry_config["retry_enabled"] = retry_times > 0
            retry_config["max_retries"] = retry_times

        retry_config.setdefault("retry_enabled", False)
        retry_config.setdefault("max_retries", 0)
        retry_config.setdefault("retry_interval", 100)

        return {
            "variables": variables,
            "method": str(config.get("method", "get")).lower(),
            "url": config.get("url", ""),
            "headers": raw_headers,
            "params": config.get("params", ""),
            "body": {"type": config.get("body_type", "none"), "data": config.get("body", "")},
            "authorization": config.get("authorization", {"type": "no-auth"}),
            "timeout": timeout,
            "ssl_verify": config.get("ssl_verify", True),
            "retry_config": retry_config,
        }


register_generator(IRNodeType.HTTP_REQUEST, HTTPRequestNodeGenerator())
