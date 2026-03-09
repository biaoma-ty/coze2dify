from __future__ import annotations

from datetime import datetime
from typing import Any

from core.coze.parser import CozeParser
from core.dify.generator import DifyGenerator
from core.ir.models import ConversionReport, IRWorkflow
from core.engine.converter import ConversionEngine


class SyncEngine:
    """Orchestrates bidirectional sync between Coze and Dify databases."""

    def __init__(self, coze_db_url: str, dify_db_url: str) -> None:
        self.coze_db_url = coze_db_url
        self.dify_db_url = dify_db_url
        self.converter = ConversionEngine()

    def execute_sync(self) -> dict[str, Any]:
        """Execute a full sync cycle."""
        result = {
            "started_at": datetime.utcnow().isoformat(),
            "workflows_synced": 0,
            "workflows_failed": 0,
            "conflicts": [],
            "errors": [],
        }

        # 1. Read all workflows from Coze DB
        coze_workflows = self._read_coze_workflows()

        # 2. Read existing synced workflows from Dify DB
        dify_existing = self._read_dify_workflows()

        # 3. Detect changes
        to_create, to_update, conflicts = self._detect_changes(coze_workflows, dify_existing)

        # 4. Process new workflows
        for wf_data in to_create:
            try:
                dsl, report = self.converter.convert_from_dict(wf_data)
                self._write_to_dify(dsl, is_update=False)
                result["workflows_synced"] += 1
            except Exception as e:
                result["workflows_failed"] += 1
                result["errors"].append(str(e))

        # 5. Process updated workflows
        for wf_data in to_update:
            try:
                dsl, report = self.converter.convert_from_dict(wf_data)
                self._write_to_dify(dsl, is_update=True)
                result["workflows_synced"] += 1
            except Exception as e:
                result["workflows_failed"] += 1
                result["errors"].append(str(e))

        result["conflicts"] = conflicts
        result["completed_at"] = datetime.utcnow().isoformat()
        return result

    def diff(self) -> dict[str, Any]:
        """Compare source and target without syncing."""
        coze_workflows = self._read_coze_workflows()
        dify_existing = self._read_dify_workflows()
        to_create, to_update, conflicts = self._detect_changes(coze_workflows, dify_existing)
        return {
            "new_workflows": len(to_create),
            "updated_workflows": len(to_update),
            "conflicts": len(conflicts),
        }

    def _read_coze_workflows(self) -> list[dict[str, Any]]:
        # TODO: Implement actual DB read via CozeDbReader
        return []

    def _read_dify_workflows(self) -> dict[str, Any]:
        # TODO: Implement actual DB read
        return {}

    def _detect_changes(self, source: list[dict], target: dict) -> tuple[list, list, list]:
        to_create: list[dict] = []
        to_update: list[dict] = []
        conflicts: list[dict] = []

        for wf in source:
            wf_id = wf.get("id", "")
            if wf_id not in target:
                to_create.append(wf)
            else:
                # Simple hash comparison for change detection
                to_update.append(wf)

        return to_create, to_update, conflicts

    def _write_to_dify(self, dsl: Any, is_update: bool = False) -> None:
        # TODO: Implement via DifyDbWriter
        pass
