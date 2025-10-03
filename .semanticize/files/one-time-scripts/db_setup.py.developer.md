# Module: `one-time-scripts/db_setup.py`

This module is designed for the **initial, one-time setup of the PostgreSQL database schema**. It reads schema definition statements from an external SQL file (`../db_schema.sql`) and executes them against the configured database.

## Dependencies

The script relies on:
1.  **`psycopg2`**: For connecting and interacting with PostgreSQL.
2.  **`python-dotenv` (`load_dotenv`)**: To load database connection parameters from environment variables (specifically `DATABASE_URL`).

## Functions

### `setup_database()`

**Summary:**
This function orchestrates the entire database schema provisioning process. It fetches connection details from the environment, establishes a connection to PostgreSQL, reads the required SQL schema definition, and executes all statements within that file to initialize the database structure.

**Big Picture:**
This is the primary entry point for bootstrapping the database structure when deploying or initializing the application environment for the first time. It ensures the necessary tables, indices, or other structural elements defined in `db_schema.sql` are present.

**Interaction Patterns:**
1.  **Environment Loading:** Calls `load_dotenv()` to load configuration.
2.  **Connection Retrieval:** Attempts to retrieve `DATABASE_URL` from environment variables. If missing, it exits gracefully.
3.  **Database Connection:** Establishes a connection using `psycopg2.connect()`. Crucially, it sets `conn.autocommit = True` to ensure schema definition commands (like `CREATE TABLE`) execute immediately without requiring an explicit transaction commit.
4.  **Schema Reading:** Reads the contents of the file located at `../db_schema.sql`. It includes error handling for `FileNotFoundError`, suggesting this script should be executed from within the `one-time-scripts/` directory relative to the schema file location.
5.  **Schema Execution:** Executes the entire concatenated SQL string via `cur.execute()`.
6.  **Cleanup:** Closes the cursor and the connection upon successful completion or handles `psycopg2.Error` exceptions during connection or execution.

**Execution Context:**
The script is intended to be run directly (as indicated by the `if __name__ == '__main__':` block) to perform its setup task.