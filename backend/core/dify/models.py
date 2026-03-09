from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DifyEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str = "source"
    targetHandle: str = "target"
    type: str = "custom"
    data: dict[str, Any] = Field(default_factory=dict)
    zIndex: int = 0


class DifyNodeData(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    title: str = ""
    desc: str = ""
    selected: bool = False


class DifyNode(BaseModel):
    id: str
    data: DifyNodeData
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    width: int = 244
    height: int = 90
    type: str = "custom"
    sourcePosition: str = "right"
    targetPosition: str = "left"
    parentId: str | None = None
    zIndex: int | None = None
    draggable: bool | None = None
    selectable: bool | None = None


class DifyGraph(BaseModel):
    nodes: list[DifyNode] = Field(default_factory=list)
    edges: list[DifyEdge] = Field(default_factory=list)
    viewport: dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "zoom": 0.7})


class DifyWorkflow(BaseModel):
    graph: DifyGraph = Field(default_factory=DifyGraph)
    features: dict[str, Any] = Field(default_factory=dict)
    conversation_variables: list[Any] = Field(default_factory=list)
    environment_variables: list[Any] = Field(default_factory=list)


class DifyDSL(BaseModel):
    version: str = "0.6.0"
    kind: str = "app"
    app: dict[str, Any] = Field(
        default_factory=lambda: {
            "mode": "workflow",
            "name": "",
            "description": "",
            "icon": "🤖",
            "icon_background": "#FFEAD5",
        }
    )
    dependencies: list[Any] = Field(default_factory=list)
    workflow: DifyWorkflow = Field(default_factory=DifyWorkflow)
