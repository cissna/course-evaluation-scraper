# Script: `one-time-scripts/run_all.sh`

This shell script is designed to simultaneously start both the backend and frontend development servers for the application. It manages the lifecycle of these processes, ensuring they run concurrently in the background and that a graceful shutdown mechanism is in place upon script termination.

## High-Level Overview

This script acts as a **local development environment launcher**. It executes two primary long-running components—the Python-based backend and the Node/NPM-based frontend—in parallel. It uses process grouping and signal trapping to ensure that when the script exits (either normally or due to an error), all spawned server processes are cleanly terminated.

## Functions

### `cleanup()`

| Aspect | Description |
| :--- | :--- |
| **Purpose** | Ensures all background processes spawned by this script are terminated gracefully when the script exits. |
| **Interaction** | This function is automatically invoked via the `EXIT` trap set below. It uses `kill 0` to send a signal (SIGTERM by default) to all processes in the current process group, effectively stopping the background servers. |
| **Big Picture** | Essential for preventing orphaned server processes from lingering after the launcher script finishes. |

## Execution Flow and Interaction Patterns

1.  **Initialization & Safety:** The script begins by setting `set -e`, which causes immediate exit if any non-backgrounded command fails.
2.  **Cleanup Setup:** The `trap cleanup EXIT` command registers the `cleanup` function to run whenever the script exits, regardless of the exit status.
3.  **Backend Launch:**
    *   The Python backend server (`python3 -m backend.app`) is started in the background (`&`).
    *   Its standard output and standard error streams are piped (`2>&1`) into a `while read` loop.
    *   This loop prefixes every line from the backend with `[backend] ` before printing it to the console, providing clear log separation.
4.  **Frontend Launch:**
    *   The script changes directory to `./frontend`.
    *   The frontend development server (`npm start`) is executed. The output is piped through `cat` (likely to ensure proper handling of the TTY/pipe interaction) before being processed by its own `while read` loop.
    *   Similar to the backend, output is prefixed with `[frontend] `.
    *   This entire pipeline is also started in the background (`&`).
5.  **Waiting:** The script pauses execution indefinitely using `wait`, which blocks until all background jobs started within the current shell have completed. Since the servers are designed to run forever, `wait` effectively keeps the script alive, monitoring the background processes until an external signal (like Ctrl+C) terminates the script, triggering the `cleanup` function.