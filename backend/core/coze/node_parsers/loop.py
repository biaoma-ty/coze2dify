from __future__ import annotations

from typing import Any

from core.ir.types import IRNodeType

from . import register_parser


class LoopNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        config: dict[str, Any] = {}
        node_type = IRNodeType.LOOP_COUNTED

        data = node.data or {}
        coze_inputs = data.get("inputs", {})
        loop_config = coze_inputs.get("loopConfig", {})

        if loop_config:
            loop_type = loop_config.get("loopType", "count")
            config["loop_type"] = loop_type
            config["max_iterations"] = loop_config.get("maxLoopTimes", 10)

            if loop_type == "array":
                node_type = IRNodeType.LOOP_ARRAY
                config["iterator_selector"] = loop_config.get("arraySelector", "")
            elif loop_type == "count":
                node_type = IRNodeType.LOOP_COUNTED
                config["loop_count"] = loop_config.get("loopTimes", 10)
            elif loop_type == "infinite":
                node_type = IRNodeType.LOOP_INFINITE
        else:
            # Real Coze exports store loop settings directly under inputs.
            loop_type = coze_inputs.get("loopType", "count")
            config["loop_type"] = loop_type

            if loop_type == "array":
                node_type = IRNodeType.LOOP_ARRAY
                input_params = coze_inputs.get("inputParameters", [])
                if input_params:
                    value = input_params[0].get("input", {}).get("value", {})
                    content = value.get("content", {})
                    if isinstance(content, dict):
                        config["iterator_selector"] = [content.get("blockID", ""), content.get("name", "")]
            elif loop_type == "count":
                loop_value = coze_inputs.get("loopCount", {}).get("value", {}).get("content")
                config["loop_count"] = int(loop_value or 10)
            elif loop_type == "infinite":
                node_type = IRNodeType.LOOP_INFINITE

        return {"node_type": node_type, "config": config}


register_parser(IRNodeType.LOOP_COUNTED, LoopNodeParser())
