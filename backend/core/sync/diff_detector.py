from __future__ import annotations

import hashlib
import json
from typing import Any


class DiffDetector:
    """Detects changes between source and target workflows."""

    @classmethod
    def compute_hash(cls, workflow_data: dict[str, Any]) -> str:
        serialized = json.dumps(cls._canonicalize_workflow_data(workflow_data), sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @classmethod
    def _canonicalize_workflow_data(cls, workflow_data: dict[str, Any]) -> dict[str, Any]:
        canonical = cls._canonicalize_dict(workflow_data)
        graph = canonical.get("graph")
        if isinstance(graph, dict):
            canonical["graph"] = cls._canonicalize_graph(graph)
        return canonical

    @classmethod
    def _canonicalize_graph(cls, graph: dict[str, Any]) -> dict[str, Any]:
        canonical = cls._canonicalize_dict(graph)
        nodes = canonical.get("nodes")
        if isinstance(nodes, list):
            canonical_nodes = [cls._canonicalize_dict(node) if isinstance(node, dict) else node for node in nodes]
            canonical["nodes"] = sorted(canonical_nodes, key=cls._sort_key)
        edges = canonical.get("edges")
        if isinstance(edges, list):
            canonical_edges = [cls._canonicalize_dict(edge) if isinstance(edge, dict) else edge for edge in edges]
            canonical["edges"] = sorted(canonical_edges, key=cls._sort_key)
        return canonical

    @classmethod
    def _canonicalize_dict(cls, payload: dict[str, Any]) -> dict[str, Any]:
        canonical: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, dict):
                canonical[key] = cls._canonicalize_dict(value)
            elif isinstance(value, list):
                canonical[key] = [
                    cls._canonicalize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                canonical[key] = value
        return canonical

    @staticmethod
    def _sort_key(item: Any) -> str:
        if isinstance(item, dict):
            primary = [
                str(item.get("id") or ""),
                str(item.get("source") or ""),
                str(item.get("target") or ""),
                str(item.get("sourceHandle") or ""),
                str(item.get("targetHandle") or ""),
            ]
            return "|".join(primary) + "|" + json.dumps(item, sort_keys=True, ensure_ascii=False)
        return json.dumps(item, sort_keys=True, ensure_ascii=False)

    def detect_changes(
        self,
        source_workflows: dict[str, dict],
        target_workflows: dict[str, dict],
    ) -> tuple[list[str], list[str], list[str]]:
        """Returns (new_ids, updated_ids, deleted_ids)."""
        source_ids = set(source_workflows.keys())
        target_ids = set(target_workflows.keys())

        new_ids = list(source_ids - target_ids)
        deleted_ids = list(target_ids - source_ids)

        updated_ids = []
        for wf_id in source_ids & target_ids:
            source_hash = self.compute_hash(source_workflows[wf_id])
            target_hash = self.compute_hash(target_workflows[wf_id])
            if source_hash != target_hash:
                updated_ids.append(wf_id)

        return new_ids, updated_ids, deleted_ids
