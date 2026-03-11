# Strict Supported Subset

This project now enforces a runtime policy called `strict_supported_subset`.

The intent is simple: correctness is more important than broad but unsafe coverage. If a Coze workflow falls outside the subset below, the converter records a blocked result and does not emit Dify DSL.

## What Is Currently Admitted

### Automatically supported

- Entry (`type: 1`) -> `start`
- Exit (`type: 2`) -> `end`
- OutputEmitter (`type: 13`) -> `answer`
- Comment (`type: 31`) -> skipped safely, no Dify node emitted

### Supported only with mandatory manual review

- Python CodeRunner (`type: 5`, `language: python3`) -> `code`

These workflows are converted and can be downloaded as DSL, but direct write to Dify is blocked until the operator explicitly confirms manual review.

## What Is Blocked

The strict subset blocks:

- every node whose design-time mapping is `Partial`, `Mode Change`, or `Unmappable`
- any node type that does not yet have semantic coverage in the test corpus
- any workflow containing such nodes, even if other nodes in the same workflow are supported

Blocked conversions:

- return `report.supported = false`
- persist `status = "blocked"`
- store no Dify DSL artifact
- disable direct write to Dify

## Test Gates Behind The Policy

The current policy is backed by four layers:

1. A 42-case Coze workflow corpus covering all mapped node classes in [`backend/tests/coze_workflow_corpus.py`](../backend/tests/coze_workflow_corpus.py).
2. Golden YAML snapshots for every currently supported mapping in [`backend/tests/golden/strict_supported_subset/`](../backend/tests/golden/strict_supported_subset/).
3. Semantic equivalence tests for supported workflows, comparing IR execution and generated Dify DSL execution on the same inputs.
4. Service and sync-path tests that verify blocked/manual-review workflows cannot slip through persistence or automated write paths.

## Operator Contract

- `supported = false`: fix the workflow or extend support coverage before exporting.
- `supported = true` and `requires_manual_review = false`: the workflow is inside the strictly verified subset.
- `supported = true` and `requires_manual_review = true`: a human must review the migration before `write-to-dify`.

This policy is intentionally conservative. It is expected to expand only when new workflow samples, semantic tests, and golden snapshots are added together.
