#!/usr/bin/env bash
# Runs the backend (FastAPI via uv/uvicorn) and frontend (Next.js via pnpm) together for local dev.
# Trap makes Ctrl+C stop both background processes.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$root/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$root/.env"
    set +a
else
    echo "warning: .env not found at $root/.env -- copy .env.example first" >&2
fi

port="${PORT:-8000}"

cleanup() {
    kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$root/backend" && uv run uvicorn app.main:app --reload --port "$port") &
backend_pid=$!

(cd "$root/frontend" && pnpm dev) &
frontend_pid=$!

echo "Backend running on port $port (pid $backend_pid), frontend pid $frontend_pid"
echo "Press Ctrl+C to stop both."

wait "$backend_pid" "$frontend_pid"
