import os
import json
import psycopg2
from dotenv import load_dotenv

def export_data_to_json():
    """
    Connects to the PostgreSQL database, fetches all course data,
    and exports it to a JSON file.
    """
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("DATABASE_URL environment variable not set.")
        return

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Fetch all data from the courses table
        cur.execute("SELECT instance_key, data FROM courses")
        rows = cur.fetchall()

        # Format the data into a dictionary
        data_export = {row[0]: row[1] for row in rows}

        # Save the data to a JSON file
        with open('data_export.json', 'w') as f:
            json.dump(data_export, f, indent=4)

        print("Data exported successfully to data_export.json")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    export_data_to_json()
