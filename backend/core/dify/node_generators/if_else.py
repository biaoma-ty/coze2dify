from __future__ import annotations

from typing import Any

from core.ir.types import IRConditionOperator, IRNodeType

from . import register_generator

_OPERATOR_MAP = {
    IRConditionOperator.EQUAL: "is",
    IRConditionOperator.NOT_EQUAL: "is not",
    IRConditionOperator.GREATER_THAN: ">",
    IRConditionOperator.GREATER_THAN_EQUAL: ">=",
    IRConditionOperator.LESS_THAN: "<",
    IRConditionOperator.LESS_THAN_EQUAL: "<=",
    IRConditionOperator.CONTAINS: "contains",
    IRConditionOperator.NOT_CONTAINS: "not contains",
    IRConditionOperator.EMPTY: "empty",
    IRConditionOperator.NOT_EMPTY: "not empty",
    IRConditionOperator.IS_TRUE: "is",
    IRConditionOperator.IS_FALSE: "is not",
    IRConditionOperator.START_WITH: "start with",
    IRConditionOperator.END_WITH: "end with",
    IRConditionOperator.IN: "in",
    IRConditionOperator.NOT_IN: "not in",
}


class IfElseNodeGenerator:
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]:
        cases: list[dict[str, Any]] = []

        for branch in ir_node.branches:
            conditions: list[dict[str, Any]] = []

            for cond in branch.conditions:
                dify_cond: dict[str, Any] = {
                    "comparison_operator": _OPERATOR_MAP.get(cond.operator, "is"),
                    "variable_selector": var_transformer.to_selector(cond.left),
                }
                if cond.right and cond.right.literal_value is not None:
                    dify_cond["value"] = cond.right.literal_value
                conditions.append(dify_cond)

            cases.append({
                "case_id": branch.branch_id,
                "logical_operator": branch.logic,
                "conditions": conditions,
            })

        return {"cases": cases}


register_generator(IRNodeType.CONDITION, IfElseNodeGenerator())
