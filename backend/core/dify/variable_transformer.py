from __future__ import annotations

from core.ir.models import IRVariableRef


class VariableTransformer:
    """Converts IR variable references to Dify variable_selector format."""

    def to_selector(self, ref: IRVariableRef) -> list[str]:
        selector = [ref.source_node_id, ref.field_name]
        selector.extend(ref.nested_path)
        return selector

    def to_template(self, ref: IRVariableRef) -> str:
        parts = [ref.source_node_id, ref.field_name] + ref.nested_path
        return "{{#" + ".".join(parts) + "#}}"
