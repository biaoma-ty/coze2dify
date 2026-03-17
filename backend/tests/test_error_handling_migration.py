from __future__ import annotations

from core.dify.generator import DifyGenerator
from core.dify.node_generators.http_request import HTTPRequestNodeGenerator
from core.engine.converter import ConversionEngine
from core.ir.models import IREdge, IRErrorHandling, IRNode, IRPosition, IRWorkflow
from core.ir.types import ErrorStrategy, IRNodeType


def test_http_request_generator_keeps_retries_disabled_by_default() -> None:
    ir_node = IRNode(
        id="http-node",
        node_type=IRNodeType.HTTP_REQUEST,
        title="HTTPRequester",
        position=IRPosition(),
        config={
            "method": "GET",
            "url": "https://example.com",
        },
    )

    payload = HTTPRequestNodeGenerator().generate(ir_node, var_transformer=None)

    assert payload["retry_config"] == {
        "retry_enabled": False,
        "max_retries": 0,
        "retry_interval": 100,
    }


def test_http_request_generator_maps_throw_retry_and_timeout_settings() -> None:
    ir_node = IRNode(
        id="http-node",
        node_type=IRNodeType.HTTP_REQUEST,
        title="HTTPRequester",
        position=IRPosition(),
        config={
            "method": "POST",
            "url": "https://example.com",
        },
        error_handling=IRErrorHandling(
            enabled=True,
            strategy=ErrorStrategy.THROW,
            retry_times=4,
            timeout_ms=2500,
        ),
    )

    payload = HTTPRequestNodeGenerator().generate(ir_node, var_transformer=None)

    assert payload["retry_config"] == {
        "retry_enabled": True,
        "max_retries": 4,
        "retry_interval": 100,
    }
    assert payload["timeout"] == {
        "max_connect_timeout": 2500,
        "max_read_timeout": 2500,
        "max_write_timeout": 2500,
    }


def test_conversion_blocks_unmappable_error_handling_on_supported_nodes() -> None:
    canvas = {
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
                                    "value": {"type": "literal", "content": "hello"},
                                },
                            }
                        ],
                        "settingOnError": {
                            "switch": True,
                            "processType": 2,
                            "retryTimes": 1,
                            "timeoutMs": 500,
                            "dataOnErr": "fallback",
                        },
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "answer"}],
        "versions": {},
    }

    _, report = ConversionEngine().convert_from_dict(canvas)

    assert report.supported is False
    assert any(
        "only preserves THROW and FAIL_BRANCH semantics on HTTP request nodes" in issue
        for issue in report.blocking_issues
    )


def test_http_request_fail_branch_strategy_preserves_exception_edge() -> None:
    workflow = IRWorkflow(
        mode="workflow",
        nodes=[
            IRNode(
                id="start",
                node_type=IRNodeType.START,
                title="Entry",
                position=IRPosition(),
            ),
            IRNode(
                id="http-node",
                node_type=IRNodeType.HTTP_REQUEST,
                title="HTTPRequester",
                position=IRPosition(),
                config={
                    "method": "GET",
                    "url": "https://example.com",
                },
                error_handling=IRErrorHandling(
                    enabled=True,
                    strategy=ErrorStrategy.FAIL_BRANCH,
                    retry_times=2,
                    timeout_ms=1200,
                ),
                source_type_name="HTTPRequester",
            ),
            IRNode(
                id="end",
                node_type=IRNodeType.END,
                title="Exit",
                position=IRPosition(),
            ),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="http-node"),
            IREdge(source_node_id="http-node", target_node_id="end", source_port="exception"),
        ],
    )

    dsl = DifyGenerator().generate(workflow)
    http_node = next(node for node in dsl.workflow.graph.nodes if node.id == "http-node")
    fail_edge = next(edge for edge in dsl.workflow.graph.edges if edge.source == "http-node" and edge.target == "end")

    assert http_node.data.retry_config == {
        "retry_enabled": True,
        "max_retries": 2,
        "retry_interval": 100,
    }
    assert http_node.data.timeout == {
        "max_connect_timeout": 1200,
        "max_read_timeout": 1200,
        "max_write_timeout": 1200,
    }
    assert fail_edge.sourceHandle == "fail-branch"


def test_conversion_blocks_http_fail_branch_without_exception_edge() -> None:
    canvas = {
        "nodes": [
            {
                "id": "start",
                "type": "1",
                "meta": {"position": {"x": 0, "y": 0}},
                "data": {"outputs": [{"type": "string", "name": "query", "required": True}]},
            },
            {
                "id": "http-node",
                "type": "45",
                "meta": {"position": {"x": 320, "y": 0}},
                "data": {
                    "inputs": {
                        "settingOnError": {
                            "switch": True,
                            "processType": 3,
                            "retryTimes": 2,
                            "timeoutMs": 900,
                        },
                    }
                },
            },
        ],
        "edges": [{"sourceNodeID": "start", "targetNodeID": "http-node"}],
        "versions": {},
    }

    _, report = ConversionEngine().convert_from_dict(canvas)

    assert report.supported is False
    assert any("no exception edge is present to preserve the fail branch" in issue for issue in report.blocking_issues)
