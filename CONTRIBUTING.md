# Contributing to coze2dify

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/biaoma-ty/coze2dify.git
cd coze2dify
make install
```

## Workflow

1. Fork the repo and create a feature branch from `main`
2. Make your changes
3. Run checks locally before every push:
   - `make check` during development
   - `make ci-local` before pushing to mirror the GitHub Actions gate
4. Optionally install the repository hook once with `make install-githooks`
5. Submit a Pull Request

## Local CI Gate

`make ci-local` is the required pre-push gate for this repository. It runs:

- backend import smoke on Python 3.10 / 3.11 / 3.12
- backend lint (`ruff check`)
- backend unit tests (`pytest`)
- frontend production build (`npm run build`)

If you want Git to enforce this automatically, run:

```bash
make install-githooks
```

That installs the repository `pre-push` hook so pushes fail fast when the local CI gate is red.

## Code Style

- **Backend**: Python, formatted with [Ruff](https://docs.astral.sh/ruff/) (`make format`)
- **Frontend**: TypeScript + React, checked with `tsc --noEmit`

## Project Structure

- `backend/core/coze/` — Coze parser and node parsers
- `backend/core/dify/` — Dify generator and node generators
- `backend/core/ir/` — Intermediate Representation models
- `frontend/src/components/` — React UI components
- `docs/` — Architecture and API documentation

## Adding a New Node Mapper

1. Create parser in `backend/core/coze/node_parsers/`
2. Create generator in `backend/core/dify/node_generators/`
3. Register mapping in `backend/core/mapper/mapping_rules.py`
4. Add test fixtures in `backend/tests/fixtures/`

## Reporting Issues

Open a [GitHub Issue](https://github.com/biaoma-ty/coze2dify/issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Coze workflow JSON (if applicable, redact sensitive data)
