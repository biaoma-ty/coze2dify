from __future__ import annotations

from typing import Any

from core.ir.models import IRBranch, IRCondition, IRVariable, IRVariableRef
from core.ir.types import IRConditionOperator, IRNodeType, IRVariableType

from ..models import CozeBlockInputReference
from . import register_parser

_OPERATOR_MAP: dict[int, IRConditionOperator] = {
    1: IRConditionOperator.EQUAL,
    2: IRConditionOperator.NOT_EQUAL,
    3: IRConditionOperator.LENGTH_GREATER_THAN,
    4: IRConditionOperator.GREATER_THAN_EQUAL,
    5: IRConditionOperator.LENGTH_LESS_THAN,
    6: IRConditionOperator.LESS_THAN_EQUAL,
    7: IRConditionOperator.CONTAINS,
    8: IRConditionOperator.NOT_CONTAINS,
    9: IRConditionOperator.EMPTY,
    10: IRConditionOperator.NOT_EMPTY,
    11: IRConditionOperator.IS_TRUE,
    12: IRConditionOperator.IS_FALSE,
    13: IRConditionOperator.GREATER_THAN,
    14: IRConditionOperator.GREATER_THAN_EQUAL,
    15: IRConditionOperator.LESS_THAN,
    16: IRConditionOperator.LESS_THAN_EQUAL,
}

_TYPE_MAP: dict[str, IRVariableType] = {
    "string": IRVariableType.STRING,
    "integer": IRVariableType.INTEGER,
    "float": IRVariableType.FLOAT,
    "number": IRVariableType.NUMBER,
    "boolean": IRVariableType.BOOLEAN,
    "object": IRVariableType.OBJECT,
    "list": IRVariableType.ARRAY,
    "array": IRVariableType.ARRAY,
}


class SelectorNodeParser:
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]:
        branches: list[IRBranch] = []
        data = node.data or {}
        inputs = data.get("inputs", {})
        conditions_data = inputs.get("conditions")
        if not conditions_data:
            conditions_data = [branch.get("condition", {}) for branch in inputs.get("branches", [])]

        for i, cond_group in enumerate(conditions_data):
            branch_id = "true" if i == 0 else f"true_{i}"
            logic_code = cond_group.get("logicType", cond_group.get("logic", 2))
            logic = "or" if logic_code == 1 else "and"

            conditions: list[IRCondition] = []
            for cond in cond_group.get("conditions", []):
                left_input = cond.get("left", {})
                if "input" in left_input:
                    left_input = left_input.get("input", {})

                left_value = left_input.get("value", {})
                left_ref = IRVariableRef(source_node_id="", field_name="")

                if left_value.get("type") in ("ref", "object_ref") and isinstance(left_value.get("content"), dict):
                    ref_data = CozeBlockInputReference.model_validate(left_value["content"])
                    left_ref = variable_resolver.resolve_reference(ref_data)

                right_var = None
                right_input = cond.get("right", {})
                if "input" in right_input:
                    right_input = right_input.get("input", {})
                right_value = right_input.get("value", {})
                if right_value.get("type") == "literal":
                    right_var = IRVariable(
                        name="",
                        var_type=_TYPE_MAP.get(right_input.get("type", "string"), IRVariableType.ANY),
                        literal_value=right_value.get("content"),
                    )

                operator_code = cond.get("operatorType", cond.get("operator", 1))
                operator = _OPERATOR_MAP.get(operator_code, IRConditionOperator.EQUAL)
                conditions.append(IRCondition(left=left_ref, operator=operator, right=right_var))

            branches.append(IRBranch(branch_id=branch_id, logic=logic, conditions=conditions))

        return {"branches": branches, "config": {}}


register_parser(IRNodeType.CONDITION, SelectorNodeParser())
