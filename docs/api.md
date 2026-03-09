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

Get conversion result.

### `GET /convert/{id}/dsl`

Download generated Dify DSL YAML file.

### `GET /convert/{id}/report`

Get detailed conversion report (mapping stats, warnings, unmappable nodes).

### `POST /convert/{id}/write-to-dify`

Direct-write conversion result to Dify PostgreSQL.

---

## Sync

### `POST /sync/config`

Create or update sync configuration (source DB + target DB connection info).

### `GET /sync/config`

Get current sync configuration.

### `POST /sync/config/test`

Test source and target database connections.

### `POST /sync/execute`

Manually trigger a sync run.

### `GET /sync/status`

Get current sync status.

### `GET /sync/history`

List sync history records.

### `GET /sync/history/{id}`

Get detailed report for a specific sync run.

### `POST /sync/schedule`

Set up scheduled sync (cron expression).

### `DELETE /sync/schedule`

Cancel scheduled sync.

### `POST /sync/diff`

Compare source/target differences without executing sync.

### `POST /sync/conflicts/{id}/resolve`

Manually resolve a sync conflict.

**Request:**
```json
{
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
