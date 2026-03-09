from __future__ import annotations

from core.ir.models import IRVariableRef

from .models import CozeBlockInputReference, CozeBlockInputValue

_SOURCE_TYPE_MAP = {
    "block-output": "node_output",
    "global_variable_app": "global_app",
    "global_variable_system": "global_system",
    "global_variable_user": "global_user",
}


class VariableResolver:
    """Transforms Coze BlockInputReference/Value into IR variable references."""

    def resolve_input_value(self, value: CozeBlockInputValue) -> IRVariableRef | None:
        if value.type == "literal":
            return None
        if value.type in ("ref", "object_ref") and isinstance(value.content, dict):
            ref_data = CozeBlockInputReference.model_validate(value.content)
            return self.resolve_reference(ref_data)
        return None

    def resolve_reference(self, ref: CozeBlockInputReference) -> IRVariableRef:
        return IRVariableRef(
            source_node_id=ref.blockID,
            field_name=ref.name,
            nested_path=ref.path,
            source_type=_SOURCE_TYPE_MAP.get(ref.source, "node_output"),
        )
