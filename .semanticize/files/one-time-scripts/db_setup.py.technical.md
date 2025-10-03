When executed this way, the `if __name__ == '__main__':` block calls `setup_database()`.

## Implementation Details

### File Path Resolution

The script relies on a **relative path**: `../db_schema.sql`. This mandates that the script must be executed from within the `one-time-scripts/` directory for the path resolution to correctly locate `db_schema.sql` in the project root directory.

### Transaction Management

By setting `conn.autocommit = True`, all DDL statements executed via `cur.execute(schema_sql)` are implicitly committed immediately. If this were set to `False` (the default), a successful execution would require an explicit `conn.commit()` call after `cur.execute()`.