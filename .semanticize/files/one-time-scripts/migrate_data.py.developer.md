# Developer Documentation for `one-time-scripts/migrate_data.py`

This script is a one-time utility designed to ingest existing course and metadata records stored in local JSON files (`data.json` and `metadata.json`) into a PostgreSQL database.

## Overview

The primary purpose of this script is to facilitate the initial population or migration of application data from a file-based source into the persistent database layer. It handles environment variable loading for database credentials, file reading, JSON parsing, and transactional insertion into two primary database tables: `course_metadata` and `courses`.

## Function Level Documentation

### `migrate_data()`

**Summary:**
Orchestrates the entire data migration process, reading data from local JSON files and inserting it into the PostgreSQL database using environment-provided connection details.

**Component Functionality:**
1.  **Environment Setup:** Loads environment variables, specifically retrieving the PostgreSQL connection string (`DATABASE_URL`). Exits if the connection string is missing.
2.  **Data Loading:** Attempts to read and parse `data.json` (containing course instance details) and `metadata.json` (containing course metadata keyed by course code) from the execution directory. Includes error handling for file not found or invalid JSON format.
3.  **Database Connection:** Establishes a connection to PostgreSQL using `psycopg2`.
4.  **Metadata Migration:** Iterates through the loaded metadata dictionary. For each entry, it attempts an `INSERT` into the `course_metadata` table, utilizing `ON CONFLICT (course_code) DO NOTHING` to prevent errors if the course code already exists. It serializes specific Python structures (like `relevant_periods`) into JSON strings before insertion.
5.  **Course Data Migration:** Iterates through the course data dictionary. For each entry, it parses the `instance_key` (e.g., `AS.180.101_FA23`) using a regular expression to extract the base `course_code` (e.g., `AS.180.101`). It then attempts an `INSERT` into the `courses` table, using `ON CONFLICT (instance_key) DO NOTHING`. The full course data payload is stored as a JSON string in the `data` column.
6.  **Transaction Management:** Commits all successful insertions or rolls back in case of database errors. Closes the cursor and connection.
7.  **Error Handling:** Catches `FileNotFoundError`, `json.JSONDecodeError`, `psycopg2.Error`, and general exceptions, printing informative messages for debugging or failure reporting.

**Big-Picture Understanding:**
This function acts as a ETL (Extract, Transform, Load) pipeline for static data bootstrapping. It ensures data integrity by using UPSERT-like behavior (`ON CONFLICT DO NOTHING`) to avoid duplicate entries based on primary/unique keys (`course_code` for metadata, `instance_key` for courses).

**High-Level Interaction Patterns:**
*   Relies on the presence of `DATABASE_URL` in the environment.
*   Requires `data.json` and `metadata.json` to be present locally.
*   Interacts with PostgreSQL via standard connection pooling/cursor management.
*   Uses regex extraction for data transformation (instance key parsing).