from __future__ import annotations

from typing import Any, Protocol

from core.ir.types import IRNodeType


class NodeParser(Protocol):
    def parse(self, node: Any, variable_resolver: Any) -> dict[str, Any]: ...


_PARSERS: dict[IRNodeType, NodeParser] = {}


def register_parser(node_type: IRNodeType, parser: NodeParser) -> None:
    _PARSERS[node_type] = parser


def get_node_parser(node_type: IRNodeType) -> NodeParser | None:
    return _PARSERS.get(node_type)
