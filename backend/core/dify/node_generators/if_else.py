from __future__ import annotations

from typing import Any

from core.ir.types import IRConditionOperator, IRNodeType, IRVariableType

from . import register_generator

_OPERATOR_MAP = {
    IRConditionOperator.EQUAL: "is",
    IRConditionOperator.NOT_EQUAL: "is not",
    IRConditionOperator.GREATER_THAN: ">",
    IRConditionOperator.GREATER_THAN_EQUAL: "≥",
    IRConditionOperator.LESS_THAN: "<",
    IRConditionOperator.LESS_THAN_EQUAL: "≤",
    IRConditionOperator.CONTAINS: "contains",
    IRConditionOperator.NOT_CONTAINS: "not contains",
    IRConditionOperator.EMPTY: "empty",
    IRConditionOperator.NOT_EMPTY: "not empty",
    IRConditionOperator.IS_TRUE: "is",
    IRConditionOperator.IS_FALSE: "is",
    IRConditionOperator.START_WITH: "start with",
    IRConditionOperator.END_WITH: "end with",
    IRConditionOperator.IN: "in",
    IRConditionOperator.NOT_IN: "not in",
}

_VAR_TYPE_MAP = {
    IRVariableType.STRING: "string",
    IRVariableType.INTEGER: "integer",
    IRVariableType.FLOAT: "number",
    IRVariableType.NUMBER: "number",
    IRVariableType.BOOLEAN: "boolean",
    IRVariableType.OBJECT: "object",
    IRVariableType.ARRAY: "array",
    IRVariableType.ARRAY_STRING: "array[string]",
    IRVariableType.ARRAY_NUMBER: "array[number]",
    IRVariableType.ARRAY_OBJECT: "array[object]",
    IRVariableType.FILE: "file",
    IRVariableType.ANY: "any",
}


class IfElseNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        cases: list[dict[str, Any]] = []

        for branch_index, branch in enumerate(ir_node.branches):
            conditions: list[dict[str, Any]] = []

            for condition_index, cond in enumerate(branch.conditions):
                var_type = "string"
                if cond.right:
                    var_type = _VAR_TYPE_MAP.get(cond.right.var_type, "any")

                dify_cond: dict[str, Any] = {
                    "id": f"{branch.branch_id}_{condition_index}",
                    "varType": var_type,
                    "comparison_operator": _OPERATOR_MAP.get(cond.operator, "is"),
                    "variable_selector": var_transformer.to_selector(cond.left),
                }
                if cond.operator == IRConditionOperator.IS_TRUE:
                    dify_cond["varType"] = "boolean"
                    dify_cond["value"] = True
                elif cond.operator == IRConditionOperator.IS_FALSE:
                    dify_cond["varType"] = "boolean"
                    dify_cond["value"] = False
                elif cond.right and cond.right.literal_value is not None:
                    dify_cond["value"] = cond.right.literal_value
                conditions.append(dify_cond)

            cases.append(
                {
                    "case_id": branch.branch_id or ("true" if branch_index == 0 else f"true_{branch_index}"),
                    "logical_operator": branch.logic,
                    "conditions": conditions,
                }
            )

        if not cases:
            cases = [{"case_id": "true", "logical_operator": "and", "conditions": []}]

        return {
            "cases": cases,
            "isInIteration": False,
            "isInLoop": False,
        }


register_generator(IRNodeType.CONDITION, IfElseNodeGenerator())
