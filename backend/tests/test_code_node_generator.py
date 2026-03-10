from core.dify.node_generators.code import CodeNodeGenerator
from core.ir.models import IRNode, IRPosition, IRVariable
from core.ir.types import IRNodeType, IRVariableType


def test_code_node_outputs_use_dify_supported_array_types() -> None:
    ir_node = IRNode(
        id="code-node",
        node_type=IRNodeType.CODE,
        title="Code Node",
        position=IRPosition(),
        outputs=[
            IRVariable(name="arr_any", var_type=IRVariableType.ARRAY),
            IRVariable(name="arr_string", var_type=IRVariableType.ARRAY_STRING),
            IRVariable(name="arr_number", var_type=IRVariableType.ARRAY_NUMBER),
            IRVariable(name="arr_object", var_type=IRVariableType.ARRAY_OBJECT),
            IRVariable(name="fallback", var_type=IRVariableType.ANY),
        ],
    )

    payload = CodeNodeGenerator().generate(ir_node, var_transformer=None)

    assert payload["outputs"] == {
        "arr_any": {"type": "array[object]"},
        "arr_string": {"type": "array[string]"},
        "arr_number": {"type": "array[number]"},
        "arr_object": {"type": "array[object]"},
        "fallback": {"type": "string"},
    }
