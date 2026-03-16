"""Regression tests for confirmed migration bugs."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.engine.conversion_service import ConversionService
from core.ir.types import IRNodeType
from db.database import Base


# ---------------------------------------------------------------------------
# 1. Selector RHS variable references
# ---------------------------------------------------------------------------

def _selector_canvas_with_rhs_ref() -> dict:
    """Condition: start.count == other.count (both sides are variable refs)."""
    return {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "integer", "name": "count", "required": True}]},
            },
            {
                "id": "other",
                "type": "5",
                "meta": {"position": {"x": 280, "y": 0}},
                "data": {
                    "inputs": {
                        "code": "def main(): return {'count': 1}",
                        "language": 1,
                        "outputParameters": [{"name": "count", "input": {"type": "integer"}}],
                    }
                },
            },
            {
                "id": "selector",
                "type": "8",
                "meta": {"position": {"x": 560, "y": 0}},
                "data": {
                    "inputs": {
                        "conditions": [
                            {
                                "logicType": 2,
                                "conditions": [
                                    {
                                        "left": {
                                            "input": {
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "start",
                                                        "name": "count",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                }
                                            }
                                        },
                                        "right": {
                                            "input": {
                                                "type": "integer",
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "other",
                                                        "name": "count",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                },
                                            }
                                        },
                                        "operatorType": 1,
                                    }
                                ],
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [
            {"sourceNodeID": "start", "targetNodeID": "other"},
            {"sourceNodeID": "other", "targetNodeID": "selector"},
        ],
        "versions": {},
    }


def test_selector_rhs_ref_preserved_in_ir() -> None:
    workflow = CozeParser().parse_dict(_selector_canvas_with_rhs_ref())
    cond = workflow.nodes[2].branches[0].conditions[0]

    assert cond.left.source_node_id == "start"
    assert cond.left.field_name == "count"

    assert cond.right is not None
    assert cond.right.ref is not None
    assert cond.right.ref.source_node_id == "other"
    assert cond.right.ref.field_name == "count"
    assert cond.right.literal_value is None


def test_selector_rhs_ref_emitted_as_selector_in_dify() -> None:
    workflow = CozeParser().parse_dict(_selector_canvas_with_rhs_ref())
    dsl = DifyGenerator().generate(workflow)

    selector_node = next(n for n in dsl.workflow.graph.nodes if n.id == "selector")
    dify_cond = selector_node.data.cases[0]["conditions"][0]

    assert dify_cond["variable_selector"] == ["start", "count"]
    # RHS ref should be emitted as a selector list, not a literal
    assert dify_cond["value"] == ["other", "count"]


def _selector_canvas_with_rhs_object_ref() -> dict:
    """Condition: start.data == other.data (object_ref on right side)."""
    canvas = _selector_canvas_with_rhs_ref()
    cond = canvas["nodes"][2]["data"]["inputs"]["conditions"][0]["conditions"][0]
    cond["right"]["input"]["value"]["type"] = "object_ref"
    cond["right"]["input"]["type"] = "object"
    return canvas


def test_selector_rhs_object_ref_preserved_in_ir() -> None:
    workflow = CozeParser().parse_dict(_selector_canvas_with_rhs_object_ref())
    cond = workflow.nodes[2].branches[0].conditions[0]

    assert cond.right is not None
    assert cond.right.ref is not None
    assert cond.right.ref.source_node_id == "other"


def test_selector_rhs_literal_still_works() -> None:
    """Literal right-side values must not regress."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "text", "required": True}]},
            },
            {
                "id": "selector",
                "type": "8",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "conditions": [
                            {
                                "logicType": 2,
                                "conditions": [
                                    {
                                        "left": {
                                            "input": {
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "start",
                                                        "name": "text",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                }
                                            }
                                        },
                                        "right": {
                                            "input": {
                                                "type": "string",
                                                "value": {"type": "literal", "content": "hello"},
                                            }
                                        },
                                        "operatorType": 1,
                                    }
                                ],
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "selector"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    cond = workflow.nodes[1].branches[0].conditions[0]
    assert cond.right is not None
    assert cond.right.literal_value == "hello"
    assert cond.right.ref is None


# ---------------------------------------------------------------------------
# 2. loopConfig.arraySelector string normalization
# ---------------------------------------------------------------------------

def test_loop_config_array_selector_string_parsed_to_list() -> None:
    """loopConfig.arraySelector as a dotted string must become a list."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "array", "name": "items", "required": True}]},
            },
            {
                "id": "loop",
                "type": "21",
                "meta": {"position": {"x": 280, "y": 0}},
                "data": {
                    "inputs": {
                        "loopConfig": {
                            "loopType": "array",
                            "arraySelector": "start.items",
                            "maxLoopTimes": 50,
                        }
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "loop"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    loop_node = workflow.nodes[1]
    assert loop_node.node_type == IRNodeType.LOOP_ARRAY
    assert loop_node.config["iterator_selector"] == ["start", "items"]


def test_loop_config_array_selector_list_passthrough() -> None:
    """loopConfig.arraySelector already a list should pass through."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "array", "name": "items", "required": True}]},
            },
            {
                "id": "loop",
                "type": "21",
                "meta": {"position": {"x": 280, "y": 0}},
                "data": {
                    "inputs": {
                        "loopConfig": {
                            "loopType": "array",
                            "arraySelector": ["start", "items"],
                        }
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "loop"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    assert workflow.nodes[1].config["iterator_selector"] == ["start", "items"]


def test_loop_config_array_selector_dify_dsl_preserves_list() -> None:
    """End-to-end: loopConfig string selector should survive into Dify DSL."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "array", "name": "items", "required": True}]},
            },
            {
                "id": "loop",
                "type": "21",
                "meta": {"position": {"x": 280, "y": 0}},
                "data": {
                    "inputs": {
                        "loopConfig": {
                            "loopType": "array",
                            "arraySelector": "start.items",
                        }
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "loop"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    dsl = DifyGenerator().generate(workflow)
    dify_loop = next(n for n in dsl.workflow.graph.nodes if n.id == "loop")
    assert dify_loop.data.iterator_selector == ["start", "items"]


# ---------------------------------------------------------------------------
# 3. BREAK / CONTINUE / UNKNOWN nodes should not emit Dify nodes
# ---------------------------------------------------------------------------

def test_generator_skips_break_node() -> None:
    from core.ir.models import IREdge, IRNode, IRPosition, IRWorkflow

    workflow = IRWorkflow(
        nodes=[
            IRNode(id="start", node_type=IRNodeType.START, position=IRPosition()),
            IRNode(id="brk", node_type=IRNodeType.BREAK, position=IRPosition(x=280, y=0)),
            IRNode(id="end", node_type=IRNodeType.END, position=IRPosition(x=560, y=0)),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="brk"),
            IREdge(source_node_id="brk", target_node_id="end"),
        ],
    )

    dsl = DifyGenerator().generate(workflow)
    node_ids = {n.id for n in dsl.workflow.graph.nodes}
    edge_pairs = {(e.source, e.target) for e in dsl.workflow.graph.edges}
    assert "start" in node_ids
    assert "end" in node_ids
    assert "brk" not in node_ids
    assert ("start", "brk") not in edge_pairs
    assert ("brk", "end") not in edge_pairs


def test_generator_skips_continue_node() -> None:
    from core.ir.models import IREdge, IRNode, IRPosition, IRWorkflow

    workflow = IRWorkflow(
        nodes=[
            IRNode(id="start", node_type=IRNodeType.START, position=IRPosition()),
            IRNode(id="cont", node_type=IRNodeType.CONTINUE, position=IRPosition(x=280, y=0)),
            IRNode(id="end", node_type=IRNodeType.END, position=IRPosition(x=560, y=0)),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="cont"),
            IREdge(source_node_id="cont", target_node_id="end"),
        ],
    )

    dsl = DifyGenerator().generate(workflow)
    node_ids = {n.id for n in dsl.workflow.graph.nodes}
    edge_pairs = {(e.source, e.target) for e in dsl.workflow.graph.edges}
    assert "cont" not in node_ids
    assert ("start", "cont") not in edge_pairs
    assert ("cont", "end") not in edge_pairs


def test_generator_skips_unknown_node() -> None:
    from core.ir.models import IREdge, IRNode, IRPosition, IRWorkflow

    workflow = IRWorkflow(
        nodes=[
            IRNode(id="start", node_type=IRNodeType.START, position=IRPosition()),
            IRNode(id="mystery", node_type=IRNodeType.UNKNOWN, position=IRPosition(x=280, y=0)),
            IRNode(id="end", node_type=IRNodeType.END, position=IRPosition(x=560, y=0)),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="mystery"),
            IREdge(source_node_id="mystery", target_node_id="end"),
        ],
    )

    dsl = DifyGenerator().generate(workflow)
    node_ids = {n.id for n in dsl.workflow.graph.nodes}
    edge_pairs = {(e.source, e.target) for e in dsl.workflow.graph.edges}
    assert "mystery" not in node_ids
    assert ("start", "mystery") not in edge_pairs
    assert ("mystery", "end") not in edge_pairs


# ---------------------------------------------------------------------------
# 4. Multiple length conditions produce parallel helper wiring
# ---------------------------------------------------------------------------

def test_multiple_length_helpers_wired_in_parallel() -> None:
    """Two length conditions should fan-out from upstream, not chain."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {
                    "outputs": [
                        {"type": "string", "name": "text", "required": True},
                        {"type": "string", "name": "name", "required": True},
                    ]
                },
            },
            {
                "id": "selector",
                "type": "8",
                "meta": {"position": {"x": 640, "y": 0}},
                "data": {
                    "inputs": {
                        "conditions": [
                            {
                                "logicType": 2,
                                "conditions": [
                                    {
                                        "left": {
                                            "input": {
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "start",
                                                        "name": "text",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                }
                                            }
                                        },
                                        "right": {
                                            "input": {
                                                "type": "integer",
                                                "value": {"type": "literal", "content": 5},
                                            }
                                        },
                                        "operatorType": 3,
                                    },
                                    {
                                        "left": {
                                            "input": {
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "start",
                                                        "name": "name",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                }
                                            }
                                        },
                                        "right": {
                                            "input": {
                                                "type": "integer",
                                                "value": {"type": "literal", "content": 3},
                                            }
                                        },
                                        "operatorType": 5,
                                    },
                                ],
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "selector"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    dsl = DifyGenerator().generate(workflow)

    edges = [(e.source, e.target) for e in dsl.workflow.graph.edges]

    # Both helpers should be reachable from start (parallel fan-out)
    assert ("start", "selector__len_1") in edges
    assert ("start", "selector__len_2") in edges

    # Both helpers should connect directly to the selector (fan-in)
    assert ("selector__len_1", "selector") in edges
    assert ("selector__len_2", "selector") in edges

    # There must be NO edge between the two helpers
    assert ("selector__len_1", "selector__len_2") not in edges
    assert ("selector__len_2", "selector__len_1") not in edges


def test_single_length_helper_still_works() -> None:
    """Single length condition should still work (no regression)."""
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "text", "required": True}]},
            },
            {
                "id": "selector",
                "type": "8",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "conditions": [
                            {
                                "logicType": 2,
                                "conditions": [
                                    {
                                        "left": {
                                            "input": {
                                                "value": {
                                                    "type": "ref",
                                                    "content": {
                                                        "blockID": "start",
                                                        "name": "text",
                                                        "path": [],
                                                        "source": "block-output",
                                                    },
                                                }
                                            }
                                        },
                                        "right": {
                                            "input": {
                                                "type": "integer",
                                                "value": {"type": "literal", "content": 5},
                                            }
                                        },
                                        "operatorType": 3,
                                    }
                                ],
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "selector"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)
    dsl = DifyGenerator().generate(workflow)

    edges = {(e.source, e.target) for e in dsl.workflow.graph.edges}
    assert ("start", "selector__len_1") in edges
    assert ("selector__len_1", "selector") in edges


# ---------------------------------------------------------------------------
# 5. write_to_dify() rejects tasks whose report is missing "supported"
# ---------------------------------------------------------------------------

MINIMAL_COZE_CANVAS = {
    "nodes": [
        {
            "id": "start-node",
            "type": "1",
            "meta": {"position": {"x": 0, "y": 0}},
            "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
        },
        {
            "id": "end-node",
            "type": "2",
            "meta": {"position": {"x": 320, "y": 0}},
            "data": {"inputs": {"terminatePlan": "useAnswerContent"}},
        },
    ],
    "edges": [{"sourceNodeID": "start-node", "targetNodeID": "end-node"}],
    "versions": {},
}


def test_write_to_dify_rejects_missing_supported_key(tmp_path, monkeypatch) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'coze2dify-safe-default.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    service = ConversionService()

    class SuccessfulWriter:
        def __init__(self, db_url: str) -> None:
            pass

        def write_workflow(self, dify_dsl) -> str:  # noqa: ANN001
            return "app-should-not-reach"

    monkeypatch.setattr("core.engine.conversion_service.DifyDbWriter", SuccessfulWriter)

    with session_factory() as db:
        conversion = service.convert_uploaded_file(
            db,
            json.dumps(MINIMAL_COZE_CANVAS).encode(),
            "safe-default.json",
        )

        # Tamper: remove "supported" from the persisted report to simulate
        # a report that was stored before the field existed.
        from db.models import MigrationTask

        task = db.get(MigrationTask, int(conversion["conversion_id"]))
        assert task is not None
        report = dict(task.report or {})
        report.pop("supported", None)
        task.report = report
        db.add(task)
        db.commit()

        with pytest.raises(ValueError, match="strict supported subset"):
            service.write_to_dify(
                db,
                conversion["conversion_id"],
                db_url="postgresql://dify.example:5432/dify",
            )
