import os
import json
import psycopg2
from dotenv import load_dotenv

def export_data_and_metadata_to_json():
    """
    Connects to the PostgreSQL database, fetches all course data and metadata,
    and exports them to separate JSON files.
    """
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("DATABASE_URL environment variable not set.")
        return

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Export course data
        cur.execute("SELECT instance_key, data FROM courses")
        rows = cur.fetchall()
        data_export = {row[0]: row[1] for row in rows}
        with open('data.json', 'w') as f:
            json.dump(data_export, f, indent=4)
        print("Course data exported successfully to data.json")

        # Export metadata
        cur.execute("SELECT course_code, last_period_gathered, last_period_failed, relevant_periods, last_scrape_during_grace_period FROM course_metadata")
        rows = cur.fetchall()
        metadata_export = {row[0]: {"last_period_gathered": row[1], "last_period_failed": row[2], "relevant_periods": row[3], "last_scrape_during_grace_period": str(row[4])} for row in rows}
        with open('metadata.json', 'w') as f:
            json.dump(metadata_export, f, indent=4)
        print("Metadata exported successfully to metadata.json")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    export_data_and_metadata_to_json()