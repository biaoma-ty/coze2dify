from __future__ import annotations

from core.ir.types import IRNodeType, MappingStatus

from .mapping_rules import MAPPING_RULES, MappingRule


class NodeMapper:
    """Central registry for node type mapping."""

    def get_rule(self, node_type: IRNodeType) -> MappingRule:
        return MAPPING_RULES.get(node_type, MappingRule(node_type, "code", MappingStatus.UNMAPPABLE, "No mapping rule"))

    def get_dify_type(self, node_type: IRNodeType) -> str:
        return self.get_rule(node_type).dify_type

    def get_status(self, node_type: IRNodeType) -> MappingStatus:
        return self.get_rule(node_type).status

    def get_all_rules(self) -> dict[IRNodeType, MappingRule]:
        return MAPPING_RULES.copy()
