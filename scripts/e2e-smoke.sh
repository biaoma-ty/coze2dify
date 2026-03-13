#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PYTHON="${COZE2DIFY_E2E_BACKEND_PYTHON:-python3.12}"
DEFAULT_DIFY_HTTP_PORT="${COZE2DIFY_E2E_DIFY_HTTP_PORT:-18080}"
DEFAULT_DIFY_DB_PORT="${COZE2DIFY_E2E_DIFY_DB_PORT:-15433}"
DEFAULT_BACKEND_PORT="${COZE2DIFY_E2E_BACKEND_PORT:-18000}"
DEFAULT_FRONTEND_PORT="${COZE2DIFY_E2E_FRONTEND_PORT:-15173}"
DIFY_HTTP_PORT=""
DIFY_DB_PORT=""
BACKEND_PORT=""
FRONTEND_PORT=""
DIFY_EMAIL="${COZE2DIFY_E2E_DIFY_EMAIL:-admin@local.test}"
DIFY_PASSWORD="${COZE2DIFY_E2E_DIFY_PASSWORD:-DifyAdmin123}"
DIFY_DB_URL=""
DIFY_BASE_URL=""
APP_BASE_URL=""
RUNTIME_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/coze2dify-e2e-XXXX")"
BACKEND_DB_PATH="$(mktemp "${TMPDIR:-/tmp}/coze2dify-backend-XXXXXX")"
DOCKER_PROJECT="coze2dify-e2e-${RANDOM}"
BACKEND_LOG="${RUNTIME_ROOT}/backend.log"
FRONTEND_LOG="${RUNTIME_ROOT}/frontend.log"

log_section() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local name="$2"
  local attempts="${3:-120}"

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  echo "Timed out waiting for ${name}: ${url}" >&2
  return 1
}

find_available_port() {
  local start_port="$1"
  "${BACKEND_PYTHON}" - "$start_port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
while port < 65535:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            port += 1
            continue
    print(port)
    break
else:
    raise SystemExit("No free TCP port found")
PY
}

dump_logs() {
  log_section "Smoke diagnostics"
  echo "Backend log:"
  if [ -f "${BACKEND_LOG}" ]; then
    tail -n 200 "${BACKEND_LOG}" || true
  else
    echo "<missing>"
  fi

  echo
  echo "Frontend log:"
  if [ -f "${FRONTEND_LOG}" ]; then
    tail -n 200 "${FRONTEND_LOG}" || true
  else
    echo "<missing>"
  fi

  echo
  echo "Dify services:"
  docker compose \
    --project-name "${DOCKER_PROJECT}" \
    -f "${ROOT_DIR}/e2e/dify/docker-compose.yml" \
    ps || true

  echo
  echo "Dify logs:"
  docker compose \
    --project-name "${DOCKER_PROJECT}" \
    -f "${ROOT_DIR}/e2e/dify/docker-compose.yml" \
    logs --tail=200 || true
}

cleanup_runtime_root() {
  if [ ! -d "${RUNTIME_ROOT}" ]; then
    return 0
  fi

  rm -rf "${RUNTIME_ROOT}" >/dev/null 2>&1 && return 0

  # Docker bind mounts may leave root-owned database files behind on CI runners.
  docker run --rm -v "${RUNTIME_ROOT}:/cleanup" busybox:latest \
    sh -c 'rm -rf /cleanup/* /cleanup/.[!.]* /cleanup/..?*' >/dev/null 2>&1 || true

  rm -rf "${RUNTIME_ROOT}" >/dev/null 2>&1 || true
}

cleanup() {
  local exit_code=$?
  set +e

  if [ "${exit_code}" -ne 0 ]; then
    dump_logs
  fi

  if [ -n "${FRONTEND_PID:-}" ]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
    wait "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi

  if [ -n "${BACKEND_PID:-}" ]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    wait "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi

  docker compose \
    --project-name "${DOCKER_PROJECT}" \
    -f "${ROOT_DIR}/e2e/dify/docker-compose.yml" \
    down -v --remove-orphans >/dev/null 2>&1 || true

  rm -f "${BACKEND_DB_PATH}" >/dev/null 2>&1 || true
  cleanup_runtime_root

  trap - EXIT
  exit "${exit_code}"
}

trap cleanup EXIT

for cmd in curl docker npm "${BACKEND_PYTHON}"; do
  require_command "${cmd}"
done

DIFY_HTTP_PORT="$(find_available_port "${DEFAULT_DIFY_HTTP_PORT}")"
DIFY_DB_PORT="$(find_available_port "${DEFAULT_DIFY_DB_PORT}")"
BACKEND_PORT="$(find_available_port "${DEFAULT_BACKEND_PORT}")"
FRONTEND_PORT="$(find_available_port "${DEFAULT_FRONTEND_PORT}")"
DIFY_DB_URL="${COZE2DIFY_E2E_DIFY_DB_URL:-postgresql://postgres:difyai123456@127.0.0.1:${DIFY_DB_PORT}/dify}"
DIFY_BASE_URL="http://127.0.0.1:${DIFY_HTTP_PORT}"
APP_BASE_URL="http://127.0.0.1:${FRONTEND_PORT}"

export DIFY_RUNTIME_ROOT="${RUNTIME_ROOT}/dify"
export DIFY_HTTP_PORT
export DIFY_DB_PORT
export DIFY_DB_USER="postgres"
export DIFY_DB_PASSWORD="difyai123456"
export DIFY_DB_NAME="dify"
export DIFY_REDIS_PASSWORD="difyai123456"
export DIFY_SECRET_KEY="sk-e2e-smoke-secret-key"
export DIFY_SANDBOX_API_KEY="dify-sandbox"
export DIFY_PLUGIN_DAEMON_KEY="local-plugin-daemon-key"
export DIFY_PLUGIN_INNER_API_KEY="local-plugin-inner-api-key"

mkdir -p \
  "${DIFY_RUNTIME_ROOT}/app-storage" \
  "${DIFY_RUNTIME_ROOT}/db-data" \
  "${DIFY_RUNTIME_ROOT}/plugin-storage" \
  "${DIFY_RUNTIME_ROOT}/redis-data" \
  "${DIFY_RUNTIME_ROOT}/sandbox-conf" \
  "${DIFY_RUNTIME_ROOT}/sandbox-dependencies"

log_section "Ensuring Playwright Chromium"
(
  cd "${ROOT_DIR}/frontend"
  npx playwright install chromium
)

log_section "Starting Dify smoke stack"
docker compose \
  --project-name "${DOCKER_PROJECT}" \
  -f "${ROOT_DIR}/e2e/dify/docker-compose.yml" \
  up -d

wait_for_http "${DIFY_BASE_URL}/console/api/setup" "Dify setup endpoint"

log_section "Bootstrapping Dify admin account"
setup_body='{"email":"'"${DIFY_EMAIL}"'","name":"Smoke Admin","password":"'"${DIFY_PASSWORD}"'","language":"en-US"}'
setup_response_file="${RUNTIME_ROOT}/dify-setup-response.json"
setup_status="$(
  curl -sS -o "${setup_response_file}" -w "%{http_code}" \
    -X POST "${DIFY_BASE_URL}/console/api/setup" \
    -H "Content-Type: application/json" \
    -d "${setup_body}"
)"
if [ "${setup_status}" != "201" ] && ! grep -q 'already_setup' "${setup_response_file}"; then
  cat "${setup_response_file}" >&2
  exit 1
fi

log_section "Starting coze2dify backend"
chmod 600 "${BACKEND_DB_PATH}" || true
(
  cd "${ROOT_DIR}/backend"
  COZE2DIFY_DATABASE_URL="sqlite:///${BACKEND_DB_PATH}" \
    "${BACKEND_PYTHON}" -m uvicorn main:app --host 127.0.0.1 --port "${BACKEND_PORT}" \
    >"${BACKEND_LOG}" 2>&1
) &
BACKEND_PID=$!

wait_for_http "http://127.0.0.1:${BACKEND_PORT}/health" "coze2dify backend"

log_section "Building coze2dify frontend"
(
  cd "${ROOT_DIR}/frontend"
  UMI_APP_API_BASE_URL="/api/v1" npm run build \
    >"${FRONTEND_LOG}" 2>&1
)

log_section "Starting coze2dify frontend"
(
  cd "${ROOT_DIR}/frontend"
  FRONTEND_PORT="${FRONTEND_PORT}" DIST_DIR="${ROOT_DIR}/frontend/dist" BACKEND_PORT="${BACKEND_PORT}" node <<'NODE' >>"${FRONTEND_LOG}" 2>&1
const fs = require("fs");
const http = require("http");
const path = require("path");
const { pipeline } = require("stream");

const distDir = process.env.DIST_DIR;
const port = Number(process.env.FRONTEND_PORT);
const backendPort = Number(process.env.BACKEND_PORT);

const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

function respondWithFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || "application/octet-stream";
  res.writeHead(200, { "Content-Type": contentType });
  fs.createReadStream(filePath).pipe(res);
}

function proxyApiRequest(req, res) {
  const upstream = http.request(
    {
      host: "127.0.0.1",
      port: backendPort,
      path: req.url,
      method: req.method,
      headers: req.headers,
    },
    (upstreamRes) => {
      res.writeHead(upstreamRes.statusCode || 502, upstreamRes.headers);
      pipeline(upstreamRes, res, () => {});
    },
  );

  upstream.on("error", (error) => {
    res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ detail: `Frontend proxy error: ${error.message}` }));
  });

  pipeline(req, upstream, () => {});
}

const server = http.createServer((req, res) => {
  if ((req.url || "").startsWith("/api/")) {
    proxyApiRequest(req, res);
    return;
  }

  const requestPath = decodeURIComponent((req.url || "/").split("?")[0]);
  const normalizedPath = requestPath === "/" ? "/index.html" : requestPath;
  const candidatePath = path.join(distDir, normalizedPath.replace(/^\/+/, ""));

  if (candidatePath.startsWith(distDir) && fs.existsSync(candidatePath) && fs.statSync(candidatePath).isFile()) {
    respondWithFile(res, candidatePath);
    return;
  }

  respondWithFile(res, path.join(distDir, "index.html"));
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Static frontend listening on http://127.0.0.1:${port}`);
});
NODE
) &
FRONTEND_PID=$!

wait_for_http "${APP_BASE_URL}" "coze2dify frontend"
wait_for_http "${APP_BASE_URL}/umi.js" "coze2dify frontend bundle"

log_section "Waiting for frontend app readiness"
(
  cd "${ROOT_DIR}/frontend"
  APP_BASE_URL="${APP_BASE_URL}" node <<'NODE'
const { chromium } = require("@playwright/test");

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    await page.goto(`${process.env.APP_BASE_URL}/migrate`, {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    await page.getByRole("heading", { name: "Import Coze Workflow" }).waitFor({
      state: "visible",
      timeout: 60_000,
    });
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
NODE
)

log_section "Running browser smoke"
(
  cd "${ROOT_DIR}/frontend"
  E2E_APP_URL="${APP_BASE_URL}" \
    E2E_DIFY_URL="${DIFY_BASE_URL}" \
    E2E_DIFY_DB_URL="${DIFY_DB_URL}" \
    E2E_DIFY_EMAIL="${DIFY_EMAIL}" \
    E2E_DIFY_PASSWORD="${DIFY_PASSWORD}" \
    E2E_FIXTURE_PATH="${ROOT_DIR}/e2e/fixtures/minimal-workflow.json" \
    npm run e2e:smoke -- --config playwright.config.ts
)

log_section "E2E smoke passed"
