-   **Language**: `plpgsql` (Procedural Language/PostgreSQL)
-   **Returns**: `TRIGGER`
-   **Description**: This function is designed to be executed by a trigger. When called, it modifies the row being updated (`NEW`) by setting its `updated_at` column to the current server timestamp (`NOW()`). It then returns the modified `NEW` row, allowing the `UPDATE` operation to proceed with the changed data.

### Triggers

Two triggers are created to automatically invoke the `trigger_set_timestamp()` function.

1.  **`set_timestamp_course_metadata`**
    ```sql
    CREATE TRIGGER set_timestamp_course_metadata
    BEFORE UPDATE ON course_metadata
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();
    ```
    -   **Event**: `BEFORE UPDATE`
    -   **Target Table**: `course_metadata`
    -   **Frequency**: `FOR EACH ROW` (The trigger fires once for every row affected by the `UPDATE` statement).
    -   **Action**: Executes the `trigger_set_timestamp()` function before the update is committed.

2.  **`set_timestamp_courses`**
    ```sql
    CREATE TRIGGER set_timestamp_courses
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE PROCEDURE trigger_set_timestamp();
    ```
    -   **Event**: `BEFORE UPDATE`
    -   **Target Table**: `courses`
    -   **Frequency**: `FOR EACH ROW`
    -   **Action**: Executes the `trigger_set_timestamp()` function.

This trigger-based mechanism ensures that any `UPDATE` operation on either table will automatically refresh the `updated_at` timestamp without requiring any explicit `SET updated_at = NOW()` clause in the application's SQL queries.