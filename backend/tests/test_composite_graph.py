from core.dify.generator import DifyGenerator
from core.engine.converter import ConversionEngine
from core.ir.models import IRBranch, IREdge, IRNode, IRPosition, IRVariable, IRWorkflow
from core.ir.types import IRNodeType, IRVariableType


def _node(
    node_id: str,
    node_type: IRNodeType,
    *,
    position: tuple[float, float] = (0, 0),
    config: dict | None = None,
    children: list[IRNode] | None = None,
    child_edges: list[IREdge] | None = None,
    outputs: list[IRVariable] | None = None,
    branches: list[IRBranch] | None = None,
) -> IRNode:
    return IRNode(
        id=node_id,
        node_type=node_type,
        title=node_type.value,
        position=IRPosition(x=position[0], y=position[1]),
        config=config or {},
        children=children or [],
        child_edges=child_edges or [],
        outputs=outputs or [],
        branches=branches or [],
        source_type_name=node_type.value,
    )


def test_conversion_report_counts_child_nodes() -> None:
    child = _node(
        "child-code",
        IRNodeType.CODE,
        outputs=[IRVariable(name="result", var_type=IRVariableType.STRING)],
    )
    iteration = _node(
        "iteration",
        IRNodeType.LOOP_ARRAY,
        config={"iterator_selector": ["start", "items"]},
        children=[child],
    )
    workflow = IRWorkflow(
        nodes=[
            _node("start", IRNodeType.START),
            iteration,
            _node("end", IRNodeType.END),
        ]
    )

    _, report = ConversionEngine().convert_from_ir(workflow)

    assert report.total_nodes == 4
    assert {result.source_node_id for result in report.node_results} == {"start", "iteration", "child-code", "end"}


def test_iteration_children_are_nested_without_return_edges() -> None:
    selector = _node(
        "selector",
        IRNodeType.CONDITION,
        position=(180, 0),
        branches=[IRBranch(branch_id="true")],
    )
    child_code = _node(
        "child-code",
        IRNodeType.CODE,
        position=(640, 0),
        outputs=[IRVariable(name="output", var_type=IRVariableType.STRING)],
    )
    iteration = _node(
        "iteration",
        IRNodeType.LOOP_ARRAY,
        position=(320, 0),
        config={"iterator_selector": ["start", "items"]},
        children=[selector, child_code],
        child_edges=[
            IREdge(source_node_id="iteration", target_node_id="selector", source_port="loop-function-inline-output"),
            IREdge(source_node_id="selector", target_node_id="child-code", source_port="true"),
            IREdge(source_node_id="child-code", target_node_id="iteration", target_port="loop-function-inline-input"),
        ],
    )
    workflow = IRWorkflow(
        nodes=[
            _node("start", IRNodeType.START),
            iteration,
            _node("end", IRNodeType.END),
        ],
        edges=[
            IREdge(source_node_id="start", target_node_id="iteration"),
            IREdge(source_node_id="iteration", target_node_id="end"),
        ],
    )

    dsl = DifyGenerator().generate(workflow)

    nodes = {node.id: node for node in dsl.workflow.graph.nodes}
    edges = dsl.workflow.graph.edges

    assert nodes["iteration"].data.start_node_id == "iterationstart"
    assert nodes["iterationstart"].parentId == "iteration"
    assert nodes["selector"].parentId == "iteration"
    assert nodes["child-code"].parentId == "iteration"
    assert any(edge.source == "iterationstart" and edge.target == "selector" for edge in edges)
    assert not any(edge.source == "child-code" and edge.target == "iteration" for edge in edges)
