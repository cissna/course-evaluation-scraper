import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    """
    Connects to the PostgreSQL database and sets up the schema.
    """
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("DATABASE_URL environment variable not set.")
        return

    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cur = conn.cursor()

        # Read the schema file
        try:
            with open('../db_schema.sql', 'r') as f:
                schema_sql = f.read()
        except FileNotFoundError:
            raise FileNotFoundError("Likely caused by not running this from the one-time-scripts/ directory")

        # Execute the schema setup
        cur.execute(schema_sql)
        print("Database schema created successfully.")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Error setting up database: {e}")

if __name__ == '__main__':
    setup_database()
