# Developer Documentation: `export_data.py`

This script is a one-time utility designed to extract current data and metadata stored in a PostgreSQL database into local JSON files for archival or external processing.

## Module Summary

The primary purpose of this module is to establish a connection to a PostgreSQL database (using credentials loaded from environment variables), execute specific SQL queries against the `courses` and `course_metadata` tables, and serialize the results into two distinct JSON files: `data.json` and `metadata.json`.

**Big Picture:** This acts as a snapshot utility for core application data residing in the database.

## Functions

### `export_data_and_metadata_to_json()`

**Summary:**
This function orchestrates the entire data export process. It loads necessary configuration (database URL), connects to PostgreSQL, performs two distinct data extractions (course records and course metadata), and writes the results to disk.

**Components & Responsibilities:**
1.  **Configuration Loading:** Loads the `DATABASE_URL` environment variable using `dotenv`.
2.  **Database Connection:** Establishes a connection to PostgreSQL using `psycopg2`.
3.  **Course Data Export:** Fetches all records from the `courses` table, mapping the `instance_key` to the `data` column, and writes the resulting dictionary to `data.json`.
4.  **Metadata Export:** Fetches key tracking fields from the `course_metadata` table, structuring the output around the `course_code`, and writes the result to `metadata.json`.
5.  **Resource Management:** Ensures the database cursor and connection are properly closed upon successful completion or failure.
6.  **Error Handling:** Catches specific `psycopg2.Error` exceptions and general exceptions during the process.

**Interaction Patterns:**
This function expects a valid `DATABASE_URL` environment variable to be set prior to execution. It follows a standard ETL pattern: Connect -> Extract (SQL) -> Transform (Python dictionary creation) -> Load (JSON file write).

**Execution Context:**
This function is intended to be called directly when the script is run via `if __name__ == '__main__':`.