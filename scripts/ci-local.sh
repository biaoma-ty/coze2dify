#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONS=(python3.10 python3.11 python3.12)
BACKEND_VENV_DIR=""

log_section() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

cleanup_backend_venv() {
  if [ -n "${BACKEND_VENV_DIR}" ] && [ -d "${BACKEND_VENV_DIR}" ]; then
    rm -rf "${BACKEND_VENV_DIR}"
  fi
}

trap cleanup_backend_venv EXIT

for cmd in curl docker git npm; do
  require_command "$cmd"
done

for py in "${PYTHONS[@]}"; do
  require_command "$py"
done

run_python_matrix_import() {
  for py in "${PYTHONS[@]}"; do
    log_section "Backend import smoke on ${py}"
    venv_dir="$(mktemp -d "${TMPDIR:-/tmp}/coze2dify-${py##python}-XXXX")"
    trap 'rm -rf "${venv_dir}"' RETURN
    "$py" -m venv "$venv_dir"
    "$venv_dir/bin/pip" install -q -e "${ROOT_DIR}/backend[dev]"
    (
      cd "${ROOT_DIR}/backend"
      "$venv_dir/bin/python" -c "from main import app; print('Import OK')"
    )
    rm -rf "${venv_dir}"
    trap - RETURN
  done
}

run_backend_checks() {
  log_section "Backend lint and tests"
  BACKEND_VENV_DIR="$(mktemp -d "${TMPDIR:-/tmp}/coze2dify-backend-XXXX")"
  python3.12 -m venv "${BACKEND_VENV_DIR}"
  "${BACKEND_VENV_DIR}/bin/pip" install -q -e "${ROOT_DIR}/backend[dev]"
  (
    cd "${ROOT_DIR}/backend"
    "${BACKEND_VENV_DIR}/bin/ruff" check .
    "${BACKEND_VENV_DIR}/bin/pytest" -q
  )
}

log_section "Python matrix import"
run_python_matrix_import

run_backend_checks

log_section "Frontend tests and build"
(
  cd "${ROOT_DIR}/frontend"
  npm run lint
  npm run test
  npx tsc --noEmit
  npm run build
)

log_section "Migration e2e smoke"
COZE2DIFY_E2E_BACKEND_PYTHON="${BACKEND_VENV_DIR}/bin/python" "${ROOT_DIR}/scripts/e2e-smoke.sh"

log_section "Local CI gate passed"
