#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to clean up background processes when the script exits
cleanup() {
    echo "Shutting down servers..."
    # Kill all processes in the process group
    kill 0
}

# Trap the EXIT signal to call the cleanup function
trap cleanup EXIT

# Start the backend server in the background and prefix its output
echo "Starting backend server..."
python3 -m backend.app 2>&1 | while IFS= read -r line; do
  echo "[backend] $line"
done &

# Start the frontend server in the background and prefix its output
echo "Starting frontend server..."
(cd frontend && npm start | cat) 2>&1 | while IFS= read -r line; do
  echo "[frontend] $line"
done &

# Wait for all background processes to finish
wait
