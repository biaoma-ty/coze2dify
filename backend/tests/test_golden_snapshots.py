from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.engine.conversion_service import ConversionService

from .coze_workflow_corpus import CORPUS_CASES

_SNAPSHOT_DIR = Path(__file__).with_name("golden").joinpath("strict_supported_subset")
_GOLDEN_CASES = [case for case in CORPUS_CASES if case.golden_snapshot]


def test_golden_snapshot_cases_exist() -> None:
    assert [case.name for case in _GOLDEN_CASES] == [
        "baseline_start_end",
        "output_emitter_passthrough",
        "output_emitter_literal_supported_duplicate",
    ]


@pytest.mark.parametrize("case", _GOLDEN_CASES, ids=lambda case: case.name)
def test_supported_cases_match_golden_yaml_snapshots(case) -> None:
    service = ConversionService()

    dsl, report = service.engine.convert_from_dict(case.canvas)

    assert report.supported is True
    assert dsl is not None
    expected_snapshot = yaml.safe_load((_SNAPSHOT_DIR / f"{case.golden_snapshot}.yml").read_text())
    actual_snapshot = yaml.safe_load(service.engine.dify_generator.to_yaml(dsl))
    assert actual_snapshot == expected_snapshot
