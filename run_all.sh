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
  npm install --no-fund --no-audit >/dev/null 2>&1
  echo "Starting frontend..."
  npm start 2>&1 | while IFS= read -r line; do
    if [[ $line == *"webpack compiled"* ]] || [[ $line == *"Compiled successfully"* ]]; then
      echo "frontend loaded on http://localhost:3000"
    elif [[ $line == *"Failed to compile"* ]] || [[ $line == *"ERROR"* ]]; then
      echo "$line"
    fi
  done
) &

# Wait for any background job to exit
wait -n || true

# Keep waiting for remaining jobs so trap can clean up
wait || true


