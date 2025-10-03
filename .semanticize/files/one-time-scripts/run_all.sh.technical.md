**Line 33:** The `wait` command pauses the execution of the main script until all background jobs started by the current shell session have terminated. Since the servers are designed to run indefinitely (until interrupted), this command effectively keeps the script alive, continuously monitoring the background processes. When the user sends an interrupt signal (Ctrl+C), the shell sends this signal to the foreground process group (which includes the script itself), triggering the `trap EXIT` handler, which then executes `cleanup`.

## Process Management and Cleanup Strategy

1.  **Process Grouping:** When the script spawns the two long-running server processes using `&`, the operating system places both the script and the new background jobs into the same **Process Group (PGID)**.
2.  **Signal Propagation:** When a user presses Ctrl+C, the terminal driver typically sends the signal (SIGINT) to the entire foreground process group.
3.  **Trap Activation:** The Bash script receives SIGINT, which causes it to exit, triggering the `trap cleanup EXIT` handler.
4.  **Graceful Termination:** The `cleanup` function executes `kill 0`. This command sends the default termination signal (SIGTERM) to every process belonging to the current process group (i.e., the script itself and both server processes), ensuring all resources are released before the script terminates completely.