from __future__ import annotations

from core.ir.models import IRVariableRef


class VariableTransformer:
    """Converts IR variable references to Dify variable_selector format."""

    def to_selector(self, ref: IRVariableRef) -> list[str]:
        if ref.source_type == "global_system":
            return ["sys", ref.field_name] + ref.nested_path
        if ref.source_type == "global_user":
            return ["conversation", ref.field_name] + ref.nested_path
        if ref.source_type == "global_app":
            return ["env", ref.field_name] + ref.nested_path
        selector = [ref.source_node_id, ref.field_name]
        selector.extend(ref.nested_path)
        return selector

    def to_template(self, ref: IRVariableRef) -> str:
        if ref.source_type == "global_system":
            parts = ["sys", ref.field_name] + ref.nested_path
        elif ref.source_type == "global_user":
            parts = ["conversation", ref.field_name] + ref.nested_path
        elif ref.source_type == "global_app":
            parts = ["env", ref.field_name] + ref.nested_path
        else:
            parts = [ref.source_node_id, ref.field_name] + ref.nested_path
        return "{{#" + ".".join(parts) + "#}}"
