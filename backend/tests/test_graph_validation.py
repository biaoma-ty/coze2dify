from core.engine.converter import ConversionEngine


def test_graph_validation_blocks_dangling_top_level_edge() -> None:
    dsl, report = ConversionEngine().convert_from_dict(
        {
            "nodes": [
                {
                    "id": "start",
                    "type": "1",
                    "meta": {"position": {"x": 0, "y": 0}},
                    "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
                },
                {
                    "id": "end",
                    "type": "2",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {"inputs": {}},
                },
            ],
            "edges": [
                {"sourceNodeID": "start", "targetNodeID": "end"},
                {"sourceNodeID": "start", "targetNodeID": "ghost"},
            ],
            "versions": {},
        }
    )

    assert dsl is None
    assert report.supported is False
    assert "missing target node 'ghost'" in report.blocking_issues[0]


def test_graph_validation_blocks_top_level_cycle() -> None:
    dsl, report = ConversionEngine().convert_from_dict(
        {
            "nodes": [
                {
                    "id": "start",
                    "type": "1",
                    "meta": {"position": {"x": 0, "y": 0}},
                    "data": {"outputs": [{"type": "string", "name": "input", "required": True}]},
                },
                {
                    "id": "answer",
                    "type": "13",
                    "meta": {"position": {"x": 320, "y": 0}},
                    "data": {
                        "inputs": {
                            "inputParameters": [
                                {
                                    "name": "answer",
                                    "input": {
                                        "type": "string",
                                        "value": {
                                            "type": "ref",
                                            "content": {
                                                "blockID": "start",
                                                "name": "input",
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
            "edges": [
                {"sourceNodeID": "start", "targetNodeID": "answer"},
                {"sourceNodeID": "answer", "targetNodeID": "start"},
            ],
            "versions": {},
        }
    )

    assert dsl is None
    assert report.supported is False
    assert any("top-level cycle" in issue for issue in report.blocking_issues)


def test_graph_validation_blocks_duplicate_node_ids() -> None:
    dsl, report = ConversionEngine().convert_from_dict(
        {
            "nodes": [
                {"id": "dup", "type": "1", "meta": {"position": {"x": 0, "y": 0}}, "data": {"outputs": []}},
                {"id": "dup", "type": "2", "meta": {"position": {"x": 320, "y": 0}}, "data": {"inputs": {}}},
            ],
            "edges": [],
            "versions": {},
        }
    )

    assert dsl is None
    assert report.supported is False
    assert any("Duplicate node id 'dup'" in issue for issue in report.blocking_issues)
