from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CozeBlockInputReference(BaseModel):
    blockID: str = ""
    name: str = ""
    path: list[str] = Field(default_factory=list)
    source: str = "block-output"


class CozeBlockInputValue(BaseModel):
    type: Literal["literal", "ref", "object_ref"] = "literal"
    content: Any = None
    rawMeta: Any = None


class CozeBlockInput(BaseModel):
    type: str = "string"
    assistType: int = 0
    schema_: Any = Field(None, alias="schema")
    value: CozeBlockInputValue | None = None

    model_config = {"populate_by_name": True}


class CozeParam(BaseModel):
    name: str = ""
    input: CozeBlockInput | None = None
    left: CozeBlockInput | None = None
    right: CozeBlockInput | None = None
    variables: list[CozeBlockInput] | None = None


class CozeSettingOnError(BaseModel):
    dataOnErr: str = ""
    switch_: bool = Field(False, alias="switch")
    processType: int | None = None
    retryTimes: int = 0
    timeoutMs: int = 0

    model_config = {"populate_by_name": True}


class CozeEdge(BaseModel):
    sourceNodeID: str
    targetNodeID: str
    sourcePortID: str = ""
    targetPortID: str = ""


class CozeNodeMeta(BaseModel):
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})


class CozeNode(BaseModel):
    id: str
    type: str
    meta: CozeNodeMeta | None = None
    data: dict[str, Any] | None = None
    blocks: list[CozeNode] = Field(default_factory=list)
    edges: list[CozeEdge] = Field(default_factory=list)
    version: str = ""


class CozeCanvas(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    mode: str = "workflow"
    nodes: list[CozeNode] = Field(default_factory=list)
    edges: list[CozeEdge] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)
