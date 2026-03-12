# Strict Supported Subset

This project now enforces a runtime policy called `strict_supported_subset`.

The goal is conservative correctness: only a small verified subset of Coze workflows is allowed to emit Dify DSL. If a workflow falls outside that subset, the converter records a blocked result and stops before DSL generation.

## What Is Currently Admitted

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
- any node type that has not yet been explicitly admitted into the supported subset
- any workflow containing such nodes, even if other nodes in the same workflow are supported

Blocked conversions:

- return `report.supported = false`
- persist `status = "blocked"`
- store no Dify DSL artifact
- disable direct write to Dify

This policy is intentionally conservative. The subset should only expand when dedicated coverage is added for the new path.
The current coverage baseline lives in `backend/tests/coze_workflow_corpus.py` and tracks 42 representative Coze node-class cases.

Coverage expectations for each admitted path now include:

1. Corpus coverage in `backend/tests/coze_workflow_corpus.py`.
2. Golden YAML snapshots for every currently supported mapping in `backend/tests/golden/strict_supported_subset/`.
3. Semantic equivalence tests for supported workflows, comparing IR execution and generated Dify DSL execution on the same inputs.
4. Service and sync-path tests that verify blocked/manual-review workflows cannot slip through persistence or automated write paths.
