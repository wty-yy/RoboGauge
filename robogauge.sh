#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed or is not available in PATH." >&2
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 127
fi

# The checkout is shared by the host and Isaac Lab containers. Python venvs
# contain interpreter-specific links, so keep each runtime under the
# repository's .venv directory and derive the subdirectory from the selected
# interpreter. This avoids hard-coded host/container paths.
ROBOGAUGE_PYTHON="$(uv python find --no-project --managed-python --resolve-links 3.11)"
ROBOGAUGE_PYTHON_VERSION="$("$ROBOGAUGE_PYTHON" --version)"
ROBOGAUGE_RUNTIME_ID="$(printf '%s\n%s' "$ROBOGAUGE_PYTHON" "$ROBOGAUGE_PYTHON_VERSION" | cksum | awk '{print $1}')"
ROBOGAUGE_ENVIRONMENT="${ROBOGAUGE_VENV:-.venv/uv-${ROBOGAUGE_RUNTIME_ID}}"
export UV_PROJECT_ENVIRONMENT="$ROBOGAUGE_ENVIRONMENT"

usage() {
    cat <<'EOF'
Usage:
  ./robogauge.sh [RUN_ARGS...]
  ./robogauge.sh -s|--server [SERVER_ARGS...]
  ./robogauge.sh -i|--install [UV_SYNC_ARGS...]

Options:
  -i, --install  Install or synchronize the full runtime with uv sync.
  -s, --server   Start robogauge/scripts/server.py.
  -h, --help     Show this help message.

All arguments following a mode are passed directly to the corresponding
command. Without a mode, arguments are passed to robogauge/scripts/run.py.

Examples:
  ./robogauge.sh -i
  ./robogauge.sh -s --port 9973 --num-processes 30
  ./robogauge.sh --task-name go2 --headless
EOF
}

ensure_environment() {
    if [[ ! -x "$ROBOGAUGE_ENVIRONMENT/bin/python" ]]; then
        echo "RoboGauge runtime not found at '$ROBOGAUGE_ENVIRONMENT'; installing it for this runtime."
        uv sync --group runtime --python "$ROBOGAUGE_PYTHON"
    fi
}

case "${1:-}" in
    -i|--install)
        shift
        exec uv sync --group runtime --python "$ROBOGAUGE_PYTHON" "$@"
        ;;
    -s|--server)
        shift
        ensure_environment
        server_args=()
        for arg in "$@"; do
            if [[ "$arg" == "-port" ]]; then
                arg="--port"
            fi
            server_args+=("$arg")
        done
        exec uv run --no-sync --group runtime python robogauge/scripts/server.py "${server_args[@]}"
        ;;
    -h|--help)
        usage
        ;;
    *)
        ensure_environment
        exec uv run --no-sync --group runtime python robogauge/scripts/run.py "$@"
        ;;
esac
