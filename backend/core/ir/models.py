from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .types import ErrorStrategy, IRConditionOperator, IRNodeType, IRVariableType, MappingStatus


class IRVariableRef(BaseModel):
    source_node_id: str
    field_name: str
    nested_path: list[str] = Field(default_factory=list)
    source_type: Literal["node_output", "global_app", "global_system", "global_user"] = "node_output"
    needs_array_drill_down: bool = False


class IRVariable(BaseModel):
    name: str
    var_type: IRVariableType
    required: bool = False
    description: str = ""
    default_value: Any = None
    literal_value: Any = None
    ref: IRVariableRef | None = None


class IRCondition(BaseModel):
    left: IRVariableRef
    operator: IRConditionOperator
    right: IRVariable | None = None


class IRBranch(BaseModel):
    branch_id: str
    logic: Literal["and", "or"] = "and"
    conditions: list[IRCondition] = Field(default_factory=list)


class IRErrorHandling(BaseModel):
    enabled: bool = False
    strategy: ErrorStrategy = ErrorStrategy.THROW
    default_value: str = ""
    retry_times: int = 0
    timeout_ms: int = 0


class IREdge(BaseModel):
    source_node_id: str
    target_node_id: str
    source_port: str = ""
    target_port: str = ""


class IRPosition(BaseModel):
    x: float = 0.0
    y: float = 0.0


class IRNode(BaseModel):
    id: str
    node_type: IRNodeType
    title: str = ""
    description: str = ""
    position: IRPosition = Field(default_factory=IRPosition)
    inputs: list[IRVariable] = Field(default_factory=list)
    outputs: list[IRVariable] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    error_handling: IRErrorHandling = Field(default_factory=IRErrorHandling)
    children: list[IRNode] = Field(default_factory=list)
    child_edges: list[IREdge] = Field(default_factory=list)
    branches: list[IRBranch] = Field(default_factory=list)
    source_type_id: str = ""
    source_type_name: str = ""


class IRWorkflow(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    mode: Literal["workflow", "chatflow"] = "workflow"
    nodes: list[IRNode] = Field(default_factory=list)
    edges: list[IREdge] = Field(default_factory=list)
    global_variables: list[IRVariable] = Field(default_factory=list)


class NodeConversionResult(BaseModel):
    source_node_id: str
    source_node_type: str
    target_node_id: str | None = None
    target_node_type: str | None = None
    status: MappingStatus
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ConversionReport(BaseModel):
    workflow_name: str = ""
    total_nodes: int = 0
    mapped_count: int = 0
    partial_count: int = 0
    unmappable_count: int = 0
    skipped_count: int = 0
    node_results: list[NodeConversionResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
