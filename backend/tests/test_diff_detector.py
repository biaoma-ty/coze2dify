from core.sync.diff_detector import DiffDetector


def test_diff_detector_treats_reordered_graph_nodes_and_edges_as_equal() -> None:
    payload_a = {
        "graph": {
            "nodes": [
                {"id": "start", "data": {"type": "start"}},
                {"id": "answer", "data": {"type": "answer"}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "answer"},
                {"id": "e2", "source": "answer", "target": "end"},
            ],
        },
        "features": {"mode": "workflow"},
    }
    payload_b = {
        "graph": {
            "nodes": [
                {"id": "answer", "data": {"type": "answer"}},
                {"id": "start", "data": {"type": "start"}},
            ],
            "edges": [
                {"id": "e2", "source": "answer", "target": "end"},
                {"id": "e1", "source": "start", "target": "answer"},
            ],
        },
        "features": {"mode": "workflow"},
    }

    assert DiffDetector.compute_hash(payload_a) == DiffDetector.compute_hash(payload_b)
