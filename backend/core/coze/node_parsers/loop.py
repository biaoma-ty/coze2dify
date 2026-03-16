from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType

from . import register_parser


def _parse_array_selector(raw: Any) -> list[str]:
    """Normalize arraySelector to ``[node_id, field_name]``."""
    if isinstance(raw, list):
        return [str(s) for s in raw]
    if isinstance(raw, str) and raw:
        parts = raw.split(".")
        if len(parts) >= 2:
            return parts
        # Single-segment string is ambiguous; preserve it as a single-element
        # list so downstream code can see the raw value instead of silently
        # discarding it.
        return [raw]
    return []


class LoopNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        config: dict[str, Any] = {}
        is_batch = getattr(node, "type", "") == "28"
        node_type = IRNodeType.BATCH if is_batch else IRNodeType.LOOP_COUNTED

        data = node.data or {}
        coze_inputs = data.get("inputs", {})
        loop_config = coze_inputs.get("loopConfig", {})

        if loop_config:
            loop_type = loop_config.get("loopType", "array" if is_batch else "count")
            config["loop_type"] = loop_type
            config["max_iterations"] = loop_config.get("maxLoopTimes", 10)

            if loop_type == "array":
                node_type = IRNodeType.BATCH if is_batch else IRNodeType.LOOP_ARRAY
                config["iterator_selector"] = _parse_array_selector(loop_config.get("arraySelector", ""))
            elif loop_type == "count" and not is_batch:
                node_type = IRNodeType.LOOP_COUNTED
                config["loop_count"] = loop_config.get("loopTimes", 10)
            elif loop_type == "infinite" and not is_batch:
                node_type = IRNodeType.LOOP_INFINITE
        else:
            # Real Coze exports store loop settings directly under inputs.
            loop_type = coze_inputs.get("loopType", "array" if is_batch else "count")
            config["loop_type"] = loop_type

            if loop_type == "array":
                node_type = IRNodeType.BATCH if is_batch else IRNodeType.LOOP_ARRAY
                input_params = coze_inputs.get("inputParameters", [])
                if input_params:
                    value = input_params[0].get("input", {}).get("value", {})
                    content = value.get("content", {})
                    if isinstance(content, dict):
                        config["iterator_selector"] = [content.get("blockID", ""), content.get("name", "")]
            elif loop_type == "count" and not is_batch:
                loop_value = coze_inputs.get("loopCount", {}).get("value", {}).get("content")
                try:
                    config["loop_count"] = int(loop_value or 10)
                except (ValueError, TypeError):
                    config["loop_count"] = 10
            elif loop_type == "infinite" and not is_batch:
                node_type = IRNodeType.LOOP_INFINITE

        return {"node_type": node_type, "config": config}


register_parser(IRNodeType.LOOP_COUNTED, LoopNodeParser())
register_parser(IRNodeType.BATCH, LoopNodeParser())
