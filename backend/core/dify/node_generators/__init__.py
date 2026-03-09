from __future__ import annotations

from typing import Any, Protocol

from core.ir.types import IRNodeType


class NodeGenerator(Protocol):
    def generate(self, ir_node: Any, var_transformer: Any) -> dict[str, Any]: ...


_GENERATORS: dict[IRNodeType, NodeGenerator] = {}


def register_generator(node_type: IRNodeType, generator: NodeGenerator) -> None:
    _GENERATORS[node_type] = generator


def get_node_generator(node_type: IRNodeType) -> NodeGenerator | None:
    return _GENERATORS.get(node_type)
