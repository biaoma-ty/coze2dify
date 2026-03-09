# Dev Mode

Dev Mode automatically detects locally deployed Coze Studio and Dify instances by scanning for `docker-compose.yaml` files and `.env` files on the host machine.

## How It Works

1. **Scan** — The `DevModeDetector` scans predefined filesystem paths for `docker-compose.yaml`
2. **Parse** — Extracts database credentials from `.env` files (e.g., `DB_USERNAME`, `POSTGRES_PASSWORD`)
3. **Construct** — Builds PostgreSQL connection URLs from the extracted config
4. **Connect** — Tests DB connectivity and API reachability

## Scanned Paths

### Dify
```
~/dify/
~/dify/docker/
/opt/dify/
~/docker/dify/
```

### Coze Studio
```
~/coze-studio/
~/coze-studio/docker/
/opt/coze-studio/
```

Custom paths can be configured via environment variables:
```bash
COZE2DIFY_DEV_MODE=true
COZE2DIFY_DEV_MODE_DIFY_PATHS='["~/my-dify", "/srv/dify"]'
COZE2DIFY_DEV_MODE_COZE_PATHS='["~/my-coze"]'
```

## Dify `.env` Variables Read

| Variable | Fallback | Default |
|----------|----------|---------|
| `DB_USERNAME` | `POSTGRES_USER` | `postgres` |
| `DB_PASSWORD` | `POSTGRES_PASSWORD` | `difyai123456` |
| `DB_HOST` | — | `localhost` |
| `DB_PORT` | — | `5432` |
| `DB_DATABASE` | `POSTGRES_DB` | `dify` |
| `NGINX_PORT` | `EXPOSE_NGINX_PORT` | `80` |

## API Endpoints

```
GET  /api/v1/devmode/status   → toggle state + detected services
GET  /api/v1/devmode/scan     → force re-scan
POST /api/v1/devmode/connect  → one-click connect all
```

## Frontend

When dev mode is enabled, a collapsible amber banner appears at the top of the Browse page showing:

- Detected service name and path
- DB / API availability badges
- **One-Click Connect** button that auto-fills the platform store with detected credentials
