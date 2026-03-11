# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: [Swagger UI](http://localhost:8000/docs) · [ReDoc](http://localhost:8000/redoc)

---

## Platform Connection

### `POST /platform/coze/connect`

Test Coze PAT credentials and return workspace list.

**Request:**
```json
{
  "access_token": "pat_xxxx",
  "api_base": "https://api.coze.com"
}
```

**Response:**
```json
{
  "connected": true,
  "workspaces": [
    { "id": "123", "name": "My Workspace" }
  ]
}
```

### `POST /platform/coze/workflows`

List workflows in a Coze workspace.

**Request:**
```json
{
  "access_token": "pat_xxxx",
  "api_base": "https://api.coze.com",
  "space_id": "123"
}
```

### `POST /platform/coze/workflows/fetch`

Fetch a single workflow for conversion.

**Request:**
```json
{
  "access_token": "pat_xxxx",
  "api_base": "https://api.coze.com",
  "workflow_id": "7xxxxx"
}
```

### `POST /platform/dify/connect`

Test Dify API/Console credentials.

**Request:**
```json
{
  "api_base": "http://localhost:80",
  "api_key": "app-xxxx"
}
```

**Response:**
```json
{
  "connected": true,
  "mode": "console",
  "total": 15
}
```

### `POST /platform/dify/apps`

List Dify apps/workflows.

**Request:**
```json
{
  "api_base": "http://localhost:80",
  "api_key": "app-xxxx"
}
```

### `POST /platform/db/connect`

Test direct database connection.

**Request:**
```json
{
  "platform": "dify",
  "db_url": "postgresql://user:pass@host:5432/dify"
}
```

### `POST /platform/db/workflows`

List workflows from database.

**Request:**
```json
{
  "platform": "coze",
  "db_url": "postgresql://user:pass@host:5432/coze"
}
```

---

## Conversion

### `POST /coze/upload`

Upload a Coze workflow file (JSON or YAML).

**Request:** `multipart/form-data` with `file` field.

### `POST /convert`

Execute conversion pipeline.

### `GET /convert/{id}`

Get conversion result, including the persisted report plus `source_graph` / `target_graph` summaries
for visual diff views.

The report now includes:

- `support_mode`
- `supported`
- `blocking_issues`

### `GET /convert/{id}/dsl`

Download generated Dify DSL YAML file.

Blocked conversions do not store a DSL artifact, so this endpoint only succeeds when `report.supported = true`.

### `GET /convert/{id}/report`

Get detailed conversion report (mapping stats, warnings, unmappable nodes).

### `POST /convert/{id}/write-to-dify`

Direct-write conversion result to Dify PostgreSQL.

Safety behavior:

- blocked conversions are rejected before any write is attempted
- raw target DB URLs are not echoed back in API-visible payloads
- successful and failed writes persist redacted target references plus last-write audit metadata
- write failures return actionable, sanitized error details

---

## Sync

### `POST /sync/config`

Create or update sync configuration (source DB + target DB connection info).

Request supports `delete_mode` with:

- `observe_only` (default)
- `approval_required`
- `soft_delete` (defined but rejected until rollback support exists)

### `GET /sync/config`

Get current sync configuration.

Safety behavior:

- stored source/target DB URLs are returned as redacted references such as `postgresql://***@host/db`
- blank DB URL fields on follow-up save/run requests keep the persisted value for the referenced `config_id`
- responses include the active `delete_policy` so operators can see rollback and approval requirements

### `POST /sync/config/test`

Test source and target database connections.

### `POST /sync/execute`

Manually trigger a sync run.

### `GET /sync/status`

Get current sync status.

### `GET /sync/history`

List sync history records.

Response includes persisted audit metadata with redacted source/target DB references plus recent failure samples when present.

### `GET /sync/history/{id}`

Get detailed report for a specific sync run.

Detailed payloads include:

- redacted source and target DB references
- latest resolution metadata for conflict handling
- sanitized failure details suitable for operator troubleshooting

### `POST /sync/schedule`

Set up scheduled sync (cron expression).

### `DELETE /sync/schedule`

Cancel scheduled sync for a persisted config.

**Query params:**

- `config_id`: sync config primary key

### `POST /sync/diff`

Compare source/target differences without executing sync.

Diff payloads include the active `delete_policy`, and delete-gap items carry structured policy metadata rather
than a generic unsupported message alone.

### `POST /sync/conflicts/{id}/resolve`

Manually resolve a sync conflict.

**Request:**
```json
{
  "history_id": "12",
  "strategy": "source_wins"
}
```

Strategies: `source_wins`, `target_wins`, `manual`

---

## Dev Mode

### `GET /devmode/status`

Return dev mode toggle state and detected local deployments.

**Response:**
```json
{
  "enabled": true,
  "detected": {
    "coze": [],
    "dify": [
      {
        "name": "dify",
        "path": "/Users/me/dify/docker",
        "db_url": "postgresql://postgres:difyai123456@localhost:5432/dify",
        "api_url": "http://localhost:80",
        "docker_compose_found": true,
        "env_file_found": true
      }
    ]
  }
}
```

### `GET /devmode/scan`

Force re-scan for local deployments (ignores dev_mode toggle).

### `POST /devmode/connect`

Auto-connect to all detected services and return connection results.

---

## Validation

### `POST /validate/coze`

Validate Coze JSON/YAML structure.

### `POST /validate/dify`

Validate Dify DSL structure.

---

## Mapping

### `GET /mapping/rules`

List all node mapping rules.

### `GET /mapping/preview/{workflow_id}`

Preview mapping analysis for a workflow.
