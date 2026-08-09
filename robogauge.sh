#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed or is not available in PATH." >&2
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 127
fi

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

case "${1:-}" in
    -i|--install)
        shift
        exec uv sync --group runtime "$@"
        ;;
    -s|--server)
        shift
        exec uv run --group runtime python robogauge/scripts/server.py "$@"
        ;;
    -h|--help)
        usage
        ;;
    *)
        exec uv run --group runtime python robogauge/scripts/run.py "$@"
        ;;
esac
