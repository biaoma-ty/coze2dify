<div align="center">

# 🔄 coze2dify

**Coze → Dify Workflow Migration Toolkit**

[![CI](https://github.com/biaoma-ty/coze2dify/actions/workflows/ci.yml/badge.svg)](https://github.com/biaoma-ty/coze2dify/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-≥3.10-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](#-docker-deployment)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<br/>

<img src="https://img.shields.io/badge/Coze-→_Dify-00D4AA?style=for-the-badge&labelColor=3b82f6&color=00d4aa" alt="Coze to Dify" />

<br/><br/>

*将 Coze 工作流转换为 Dify DSL / graph，当前重点是稳定迁移链路而不是完整平台产品。*

*Convert Coze workflows into Dify DSL / graph. The current focus is migration correctness, not a fully finished platform product.*

<br/>

[快速开始](#-quick-start) · [功能特性](#-features) · [架构设计](#-architecture) · [API 文档](#-api-reference) · [开发指南](#-development)

---

</div>

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🔄 **Workflow Conversion** | ✅ Verified | Coze JSON/YAML → IR → Dify graph / DSL |
| 📂 **File Import + DSL Export** | ✅ Verified | Upload local workflow file and export generated DSL |
| 🗺️ **Node Mapping** | 🟡 Strict Subset | Runtime only emits DSL for the verified supported subset; partial and unmappable nodes are blocked |
| 🔀 **Variable Transform** | 🟡 Partial | Common `BlockInputReference` cases work; edge cases still exist |
| 📋 **Conversion Report** | ✅ Verified | Mapping stats plus strict-subset support status, blocking issues, and manual-review gates |
| 🗄️ **Direct Dify DB Write** | 🟡 Guarded | Only allowed for supported conversions; high-risk nodes require explicit manual-review confirmation |
| 📊 **Visual Diff** | 🟡 Basic | Current UI shows report + mapping table, not a full graph diff |
| 🔍 **Platform Browse** | 🚧 In Progress | Connection UI exists, workflow selection flow is not completed |
| 🛠️ **Dev Mode** | 🟡 Experimental | Local service detection exists, but one-click workflow operations are limited |
| 🔁 **Incremental Sync** | 🟡 Experimental | Manual sync, diff preview, conflict resolution, and cron scheduling are wired for DB-to-DB workflows |

## 📌 Current Status

- **Verified path**: file-based Coze workflow conversion into Dify graph / DSL for the strict supported subset.
- **Verified in local testing**: migrated workflow can be written into a local Dify PostgreSQL instance and opened in Dify.
- **Strict runtime policy**: partial and unmappable nodes are blocked instead of emitting best-effort DSL.
- **Manual-review gate**: Python `CodeRunner` conversions are allowed only with explicit human confirmation before direct write.
- **Coverage baseline**: a 42-case Coze workflow corpus, semantic equivalence checks, and golden snapshots back the current support boundary.
- **Partially built**: platform browse, dev mode helpers, and direct-write UI.
- **Not production-ready yet**: incremental sync, migration history persistence, and several API/database import flows.

If you are evaluating the project, treat it as a working migration core with unfinished product surface area.

## ✅ Strict Supported Subset

The current runtime contract is intentionally conservative. Automatic DSL generation is admitted only for:

- Entry (`start`)
- Exit (`end`)
- OutputEmitter (`answer`)
- Comment (`skipped safely`)

Python `CodeRunner` nodes are admitted only with a hard manual-review gate before `write-to-dify`.

Everything else that is still marked as partial, mode-change, or unmappable in the 42-type mapping table is blocked at conversion time. See [`docs/supported-subset.md`](docs/supported-subset.md).

## 🏗️ Architecture

```
┌─────────────────┐                              ┌──────────────────┐
│  Coze Source     │                              │  Dify Target     │
│  ┌────────────┐  │                              │  ┌────────────┐  │
│  │ JSON/YAML  │──┤                         ┌───→│  │ DSL YAML   │  │
│  │ API Fetch* │──┤  CozeParser → IR → DifyGen   │  │ DB Write*  │  │
│  │ DB Reader* │──┤       │         │       └───→│  │ API Push*  │  │
│  └────────────┘  │  Validator  Validator        │  └────────────┘  │
└─────────────────┘                              └──────────────────┘
```

`*` Experimental or partially wired.

### Why IR (Intermediate Representation)?

- **Decoupled** — Coze parsing and Dify generation are fully independent
- **Extensible** — Add LangFlow, Flowise support by adding new Parser/Generator
- **Testable** — Each layer can be tested independently
- **Multi-IO** — Parser handles "how to read", Generator handles "how to write"

## 🚀 Quick Start

### Prerequisites

- Python ≥ 3.10
- Node.js ≥ 18
- PostgreSQL 16 (optional, for local Dify write testing)

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/biaoma-ty/coze2dify.git
cd coze2dify
docker compose up -d
```

Services:
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

### Option 2: Local Development

```bash
# Backend
cd backend
pip install -e ".[dev]"
python -m alembic upgrade head
uvicorn main:app --reload

# Frontend (another terminal)
cd frontend
npm install
npm run dev
```

If you already have a local `coze2dify.db` that was created by the old startup-time `create_all()` path, run `python -m alembic stamp head` once before applying future migrations.

## 📖 API Reference

### Platform Connection

Some endpoints below exist in the API surface but are not all fully wired in the frontend flow yet.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/platform/coze/connect` | Test Coze PAT token |
| `POST` | `/api/v1/platform/coze/workflows` | List Coze workflows |
| `POST` | `/api/v1/platform/dify/connect` | Test Dify API connection |
| `POST` | `/api/v1/platform/dify/apps` | List Dify apps |
| `POST` | `/api/v1/platform/db/connect` | Test DB connection |

### Conversion

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/coze/upload` | Upload Coze workflow file |
| `POST` | `/api/v1/convert` | Execute conversion |
| `GET`  | `/api/v1/convert/{id}/dsl` | Download Dify DSL |
| `POST` | `/api/v1/convert/{id}/write-to-dify` | Write converted DSL directly to Dify PostgreSQL (`confirm_reviewed` required for manual-review cases) |

### Sync

The sync API covers persisted config, manual execution, diff preview, conflict resolution, and cron scheduling.
Delete gaps are governed by an explicit policy layer; see [`docs/delete-sync-policy.md`](docs/delete-sync-policy.md).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/sync/config` | Persist sync config |
| `POST` | `/api/v1/sync/execute` | Execute manual sync and persist history |
| `GET`  | `/api/v1/sync/status` | Latest status + scheduled jobs |
| `GET`  | `/api/v1/sync/history` | List persisted sync runs |
| `POST` | `/api/v1/sync/schedule` | Register cron-based sync |
| `POST` | `/api/v1/sync/diff` | Preview create/update/conflict/delete gaps |
| `POST` | `/api/v1/sync/conflicts/{id}/resolve` | Resolve a persisted conflict |

### Safety Notes

- Sync config and direct-write responses no longer echo raw database URLs; API payloads return redacted `display_url` references instead.
- Persisted sync runs and conversion tasks now carry operator audit metadata, including redacted source/target DB references, delete-policy metadata, and the latest write attempt details.
- Reusing a saved sync config from the UI does not require re-entering the stored DB URL; leaving the redacted field blank keeps the persisted value unchanged.
- Direct DB writes and sync remain operator-driven workflows. Treat them as privileged actions, and keep them behind trusted environments and credentials management.

### Dev Mode

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/devmode/status` | Dev mode status + detected services |
| `GET`  | `/api/v1/devmode/scan` | Re-scan local deployments |
| `POST` | `/api/v1/devmode/connect` | One-click connect all detected services |

> Full interactive docs available at `/docs` (Swagger UI) or `/redoc`.

## 🗺️ Node Mapping (42 types)

The mapping table is the design target. Runtime enforcement is stricter: only the subset documented in [`docs/supported-subset.md`](docs/supported-subset.md) is currently allowed to emit DSL.

| Coze Node | Dify Node | Level |
|-----------|-----------|-------|
| Entry | `start` | 🟢 Direct |
| Exit | `end` | 🟢 Direct |
| LLM | `llm` | 🟡 Partial |
| Plugin | `tool` | 🟡 Partial |
| CodeRunner | `code` | 🟡 Partial |
| KnowledgeRetriever | `knowledge-retrieval` | 🟡 Partial |
| Selector | `if-else` | 🟡 Partial |
| HTTPRequester | `http-request` | 🟡 Partial |
| Loop | `loop` / `iteration` | 🔵 Mode Change |
| Batch | `iteration` (parallel) | 🔵 Mode Change |
| IntentDetector | `question-classifier` | 🟡 Partial |
| TextProcessor | `template-transform` / `code` | 🟡 Partial |
| VariableAggregator | `variable-aggregator` | 🟢 Direct |
| VariableAssigner | `assigner` | 🟢 Direct |
| OutputEmitter | `answer` | 🟢 Direct |
| SubWorkflow | `tool` (workflow-as-tool) | 🔵 Mode Change |
| Continue | — | 🔴 Unmappable |
| Comment | — | ⚪ Skipped |

> See the full 42-type mapping in [`docs/node-mapping.md`](docs/node-mapping.md). Strict runtime policy is documented in [`docs/supported-subset.md`](docs/supported-subset.md). Architecture details in [`docs/architecture.md`](docs/architecture.md). API reference in [`docs/api.md`](docs/api.md). Delete policy guide in [`docs/delete-sync-policy.md`](docs/delete-sync-policy.md). Dev Mode guide in [`docs/dev-mode.md`](docs/dev-mode.md).

## 📁 Project Structure

```
coze2dify/
├── Makefile                   # Dev commands
├── docker-compose.yml         # Docker orchestration
├── .github/workflows/         # CI/CD
│   └── ci.yml
├── docs/                      # Documentation
│   ├── architecture.md        #   IR pipeline design
│   ├── node-mapping.md        #   42-type mapping reference
│   ├── supported-subset.md    #   strict runtime support policy
│   ├── api.md                 #   REST API reference
│   └── dev-mode.md            #   Dev mode guide
│
├── backend/
│   ├── Dockerfile
│   ├── main.py                # FastAPI entrypoint
│   ├── config.py              # Settings (env-based)
│   ├── api/endpoints/         # REST endpoints
│   │   ├── platform.py        #   Coze/Dify connection
│   │   ├── devmode.py         #   Local deployment detection
│   │   ├── conversion.py      #   Workflow conversion
│   │   ├── sync.py            #   Bi-directional sync
│   │   └── validation.py      #   Schema validation
│   ├── core/
│   │   ├── ir/                # Intermediate Representation
│   │   ├── coze/              # Coze parser + API client
│   │   ├── dify/              # Dify generator + DB writer
│   │   ├── devmode/           # Local deployment detector
│   │   ├── mapper/            # Node type mapping registry
│   │   ├── sync/              # Sync engine + conflict resolver
│   │   └── engine/            # Conversion pipeline
│   └── tests/
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf             # Production nginx config
    └── src/
        ├── pages/             # Route pages
        │   ├── UploadPage     #   Step 1: Source config
        │   ├── BrowsePage     #   Platform browser
        │   ├── MappingPage    #   Step 2: Node mapping
        │   ├── DiffPage       #   Step 3: Visual diff
        │   ├── ResultPage     #   Step 4: Download/write
        │   └── SyncPage       #   Sync dashboard
        ├── components/
        │   ├── browser/       # Platform connect panel
        │   ├── devmode/       # Dev mode banner
        │   ├── graph/         # React Flow nodes
        │   ├── mapping/       # Mapping table
        │   └── sync/          # Sync UI
        ├── store/             # Zustand state
        ├── api/               # Axios clients
        └── types/             # TypeScript types
```

## 🛠️ Development

### Make Commands

```bash
make help            # Show all available commands
make install         # Install all dependencies (backend + frontend)
make dev             # Start backend + frontend dev servers
make dev-backend     # Start backend only
make dev-frontend    # Start frontend only
make build           # Production build
make test            # Run all tests (pytest + tsc)
make lint            # Lint all (ruff + tsc)
make format          # Auto-format backend (ruff)
make check           # Full check: lint + test + build
make ci-local        # Local CI gate before push (imports + lint + tests + build + e2e smoke)
make e2e-smoke       # Browser-level migration smoke against an ephemeral Dify stack
make install-githooks # Install repo pre-push hook
make docker-up       # Start via Docker Compose
make docker-down     # Stop Docker services
make docker-build    # Build Docker images
make docker-logs     # Tail Docker logs
make clean           # Clean build artifacts
```

### Manual Setup

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn main:app --reload --port 8000

# Frontend (another terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COZE2DIFY_DATABASE_URL` | `postgresql://localhost:5432/coze2dify` | Project DB |
| `COZE2DIFY_COZE_API_BASE` | `https://api.coze.com` | Coze API endpoint |
| `COZE2DIFY_COZE_ACCESS_TOKEN` | — | Coze PAT token |
| `COZE2DIFY_DIFY_API_BASE` | — | Dify instance URL |
| `COZE2DIFY_DIFY_API_KEY` | — | Dify API key |
| `COZE2DIFY_DIFY_DATABASE_URL` | — | Dify PostgreSQL URL |
| `COZE2DIFY_COZE_DATABASE_URL` | — | Coze PostgreSQL URL |
| `COZE2DIFY_DEV_MODE` | `false` | Enable local deployment detection |

## 🔧 CI/CD

GitHub Actions pipeline runs on every push and PR:

- **Backend**: Python 3.10/3.11/3.12 × lint (ruff) + unit tests (pytest)
- **Frontend**: Node 18/20 × typecheck (tsc) + build (vite)
- **Migration smoke**: Playwright uploads a reproducible Coze fixture, writes it into an ephemeral Dify 1.13.0 stack, opens the Dify workflow page, and fails on `console.error` / uncaught exceptions
- **Docker**: Build validation for both services

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for details.

Before pushing a branch, run `make ci-local`. It mirrors the critical GitHub Actions checks locally and is also available as the repository pre-push hook via `make install-githooks`.

### Local Smoke Reproduction

`make e2e-smoke` boots an isolated Dify stack on temporary ports, starts the local backend/frontend, and runs the browser smoke gate end to end.

Requirements:

- Docker with `docker compose`
- frontend dependencies installed (`npm install` in `frontend/`)
- a Python environment with backend deps; `make ci-local` provisions one automatically, or you can run `pip install -e "backend[dev]"` first
- Playwright Chromium; the smoke script installs it on demand

Default ports used by the smoke gate:

- coze2dify backend: `127.0.0.1:18000`
- coze2dify frontend: `127.0.0.1:15173`
- ephemeral Dify web: `127.0.0.1:18080`
- ephemeral Dify Postgres: `127.0.0.1:15433`

Passing CI means lint, unit tests, builds, and the migration smoke gate pass in CI. It still does not mean every advertised UI/API workflow is complete.

## 📄 License

Apache License 2.0

---

<div align="center">

**Built with** &nbsp;
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square)
![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black&style=flat-square)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white&style=flat-square)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?logo=postgresql&logoColor=white&style=flat-square)
![Vite](https://img.shields.io/badge/-Vite-646CFF?logo=vite&logoColor=white&style=flat-square)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white&style=flat-square)

</div>
