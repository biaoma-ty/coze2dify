from __future__ import annotations

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.engine.converter import ConversionEngine
from core.dify.variable_transformer import VariableTransformer


def test_parse_and_generate_workflow_level_state_variables() -> None:
    canvas = {
        "id": "wf-chatflow-vars",
        "name": "Chatflow With State",
        "mode": "chatflow",
        "variables": [
            {
                "name": "api_key",
                "type": "string",
                "source": "global_variable_app",
                "description": "API key",
                "defaultValue": "secret",
            },
            {
                "name": "memory",
                "type": "string",
                "source": "global_variable_user",
                "description": "Conversation memory",
                "default": "",
            },
        ],
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "query", "required": True}]},
            },
            {
                "id": "answer",
                "type": "13",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "inputParameters": [
                            {
                                "name": "text",
                                "input": {
                                    "type": "string",
                                    "value": {
                                        "type": "ref",
                                        "content": {
                                            "blockID": "",
                                            "name": "memory",
                                            "path": [],
                                            "source": "global_variable_user",
                                        },
                                    },
                                },
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
        "versions": {},
    }

    workflow = CozeParser().parse_dict(canvas)

    assert [(variable.scope, variable.name) for variable in workflow.global_variables] == [
        ("global_app", "api_key"),
        ("global_user", "memory"),
    ]

    dsl = DifyGenerator().generate(workflow)

    assert dsl.workflow.environment_variables == [
        {
            "name": "api_key",
            "value_type": "string",
            "value": "secret",
            "description": "API key",
        }
    ]
    assert dsl.workflow.conversation_variables == [
        {
            "name": "memory",
            "value_type": "string",
            "value": "",
            "description": "Conversation memory",
            "selector": ["conversation", "memory"],
        }
    ]


def test_variable_transformer_maps_global_user_refs_to_conversation_scope() -> None:
    workflow = CozeParser().parse_dict(
        {
            "mode": "chatflow",
            "variables": [{"name": "memory", "type": "string", "source": "global_variable_user"}],
            "nodes": [
                {
                    "id": "start",
                    "type": "1",
                    "meta": {"position": {"x": 0, "y": 0}},
                    "data": {"outputs": [{"type": "string", "name": "query", "required": True}]},
                },
                {
                    "id": "answer",
                    "type": "13",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {
                        "inputs": {
                            "inputParameters": [
                                {
                                    "name": "text",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "",
                                                "name": "memory",
                                                "path": [],
                                                "source": "global_variable_user",
                                            },
                                        },
                                    },
                                }
                            ]
                        }
                    },
                },
            ],
            "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
            "versions": {},
        }
    )
    ref = workflow.nodes[1].inputs[0].ref

    assert ref is not None
    transformer = VariableTransformer()
    assert transformer.to_selector(ref) == ["conversation", "memory"]
    assert transformer.to_template(ref) == "{{#conversation.memory#}}"


def test_conversion_blocks_undefined_global_state_references() -> None:
    canvas = {
        "mode": "chatflow",
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "query", "required": True}]},
            },
            {
                "id": "answer",
                "type": "13",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "inputParameters": [
                            {
                                "name": "text",
                                "input": {
                                    "type": "string",
                                    "value": {
                                        "type": "ref",
                                        "content": {
                                            "blockID": "",
                                            "name": "api_key",
                                            "path": [],
                                            "source": "global_variable_app",
                                        },
                                    },
                                },
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
        "versions": {},
    }

    _, report = ConversionEngine().convert_from_dict(canvas)

    assert report.supported is False
    assert any("Global variable reference 'api_key'" in issue for issue in report.blocking_issues)


def test_conversion_blocks_conversation_state_in_workflow_mode() -> None:
    canvas = {
        "mode": "workflow",
        "variables": [{"name": "memory", "type": "string", "source": "global_variable_user"}],
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "query", "required": True}]},
            },
            {
                "id": "answer",
                "type": "13",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "inputParameters": [
                            {
                                "name": "text",
                                "input": {
                                    "type": "string",
                                    "value": {
                                        "type": "ref",
                                        "content": {
                                            "blockID": "",
                                            "name": "memory",
                                            "path": [],
                                            "source": "global_variable_user",
                                        },
                                    },
                                },
                            }
                        ]
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
        "versions": {},
    }

    _, report = ConversionEngine().convert_from_dict(canvas)

    assert report.supported is False
    assert any("requires chatflow mode" in issue for issue in report.blocking_issues)
