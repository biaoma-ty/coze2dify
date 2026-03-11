from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.ir.types import IRConditionOperator, IRNodeType


def test_batch_nodes_preserve_parallel_iteration_semantics() -> None:
    workflow = CozeParser().parse_dict(
        {
            "nodes": [
                {
                    "id": "start",
                    "type": "1",
                    "meta": {"position": {"x": 0, "y": 0}},
                    "data": {
                        "inputs": {},
                        "outputs": [{"type": "array", "name": "items", "required": True}],
                    },
                },
                {
                    "id": "batch",
                    "type": "28",
                    "meta": {"position": {"x": 280, "y": 0}},
                    "data": {
                        "inputs": {
                            "inputParameters": [
                                {
                                    "name": "items",
                                    "input": {
                                        "type": "array",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "start",
                                                "name": "items",
                                                "path": [],
                                                "source": "block-output",
                                            },
                                        },
                                    },
                                }
                            ]
                        }
                    },
                },
            ],
            "edges": [{"sourceNodeID": "start", "targetNodeID": "batch"}],
            "versions": {},
        }
    )

    batch_node = workflow.nodes[1]
    assert batch_node.node_type == IRNodeType.BATCH
    assert batch_node.config["loop_type"] == "array"
    assert batch_node.config["iterator_selector"] == ["start", "items"]
    assert "loop_count" not in batch_node.config

    dsl = DifyGenerator().generate(workflow)
    dify_batch = next(node for node in dsl.workflow.graph.nodes if node.id == "batch")
    assert dify_batch.data.type == "iteration"
    assert dify_batch.data.is_parallel is True
    assert dify_batch.data.iterator_selector == ["start", "items"]


def test_selector_length_conditions_insert_helper_code_nodes() -> None:
    workflow = CozeParser().parse_dict(
        {
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
    )

    selector_node = workflow.nodes[1]
    assert selector_node.branches[0].conditions[0].operator == IRConditionOperator.LENGTH_GREATER_THAN

    dsl = DifyGenerator().generate(workflow)
    nodes = {node.id: node for node in dsl.workflow.graph.nodes}
    helper_node = nodes["selector__len_1"]
    selector_dify_node = nodes["selector"]

    assert helper_node.data.type == "code"
    assert helper_node.data.variables == [{"variable": "value", "value_selector": ["start", "text"]}]
    assert helper_node.data.outputs == {"length_1": {"type": "number"}}
    assert "len(value)" in helper_node.data.code

    selector_condition = selector_dify_node.data.cases[0]["conditions"][0]
    assert selector_condition["comparison_operator"] == ">"
    assert selector_condition["variable_selector"] == ["selector__len_1", "length_1"]

    edges = {(edge.source, edge.target) for edge in dsl.workflow.graph.edges}
    assert ("start", "selector__len_1") in edges
    assert ("selector__len_1", "selector") in edges
