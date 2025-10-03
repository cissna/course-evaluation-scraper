# Database Schema: `db_schema.sql`

This document provides a developer-level overview of the PostgreSQL database schema used in the JHU Course Evaluation Analyzer.

## High-Level Summary

The database is designed to efficiently store and manage course evaluation data by separating high-level course metadata from the detailed, instance-specific evaluation data. This two-table structure (`course_metadata` and `courses`) allows the application to quickly check the status of a course's data without needing to load the large JSON payloads associated with each evaluation.

A database function and associated triggers are used to automatically manage `updated_at` timestamps, simplifying the application logic by offloading this responsibility to the database itself.

---

## Components

### `course_metadata` Table

-   **Purpose**: Acts as a central registry and state-tracking table for every unique course in the system. It stores metadata related to the scraping process, such as which academic periods have been scraped and when the last attempt was made.
-   **Interaction**:
    -   The backend services query this table to determine if a course's data is stale and needs to be re-scraped.
    -   After a scraping operation, the backend updates the `last_period_gathered`, `relevant_periods`, and other tracking fields in this table.
    -   It provides a quick lookup to see what data is available for a given `course_code` without accessing the larger `courses` table.

### `courses` Table

-   **Purpose**: Stores the raw, detailed evaluation data for each specific instance of a course (i.e., a course from a particular semester and instructor).
-   **Key Columns**:
    -   `instance_key`: The primary key, uniquely identifying a single course offering (e.g., `AS.180.101_FA23`).
    -   `course_code`: A foreign key that links the course instance back to its corresponding entry in the `course_metadata` table.
    -   `data`: A JSONB column that holds the entire scraped evaluation data for that instance. Using JSONB is efficient for storage and allows for potential querying within the JSON structure if needed in the future.
-   **Interaction**:
    -   The backend writes new records to this table after successfully scraping evaluation data for a course instance.
    -   When the frontend requests data for analysis, the backend retrieves all relevant records from this table, aggregates them, and sends the raw data to the client.

### `trigger_set_timestamp()` Function & Triggers

-   **Purpose**: An automated database mechanism to ensure the `updated_at` field in both `course_metadata` and `courses` is always current.
-   **Interaction**:
    -   This PostgreSQL function is automatically executed by a trigger *before* any `UPDATE` operation on a row in either table.
    -   It sets the `updated_at` column to the current time (`NOW()`).
    -   This pattern simplifies the backend application code, as developers do not need to manually set the `updated_at` field when performing database updates. It guarantees that the timestamp accurately reflects the last modification time at the database level.