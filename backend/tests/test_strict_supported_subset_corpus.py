from __future__ import annotations

import pytest

from core.engine.conversion_service import ConversionService

from .coze_workflow_corpus import CORPUS_CASES


def test_strict_subset_corpus_contains_42_cases() -> None:
    assert len(CORPUS_CASES) == 42
    assert len({case.name for case in CORPUS_CASES}) == 42


@pytest.mark.parametrize("case", CORPUS_CASES, ids=lambda case: case.name)
def test_strict_subset_corpus_matches_current_support_boundary(case) -> None:
    service = ConversionService()

    dsl, report = service.engine.convert_from_dict(case.canvas)

    assert report.supported is case.expected_supported
    assert (dsl is not None) is case.expected_supported
    if case.expected_supported:
        assert report.blocking_issues == []
    else:
        assert report.blocking_issues
