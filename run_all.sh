#!/usr/bin/env bash

set -euo pipefail

# Kill child processes on exit/interrupt
cleanup() {
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Start backend
python3 backend/app.py &

# Start frontend
(
  cd frontend
  npm install --no-fund --no-audit
  npm start
) &

# Wait for any background job to exit
wait -n || true

# Keep waiting for remaining jobs so trap can clean up
wait || true


