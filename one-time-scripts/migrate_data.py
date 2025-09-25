import os
import json
import psycopg2
from dotenv import load_dotenv

def migrate_data():
    """
    Migrates data from local JSON files to the PostgreSQL database.
    """
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("DATABASE_URL environment variable not set.")
        return

    # Load data from JSON files
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        with open('metadata.json', 'r') as f:
            metadata = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure 'data.json' and 'metadata.json' are in the same directory.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}.")
        return

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Migrate metadata
        for course_code, meta in metadata.items():
            cur.execute(
                """
                INSERT INTO course_metadata (course_code, last_period_gathered, last_period_failed, relevant_periods, last_scrape_during_grace_period)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (course_code) DO NOTHING;
                """,
                (
                    course_code,
                    meta.get('last_period_gathered'),
                    meta.get('last_period_failed', False),
                    json.dumps(meta.get('relevant_periods')),
                    meta.get('last_scrape_during_grace_period')
                )
            )
        print("Metadata migration complete.")

        # Migrate course data
        for instance_key, course_data in data.items():
            # Extract course_code from instance_key (e.g., AS.180.101 from AS.180.101_FA23)
            import re
            match = re.match(r'([A-Z]{2}\.\d{3}\.\d{3})', instance_key)
            if match:
                course_code = match.group(1)
            else:
                print(f"Warning: Could not extract course_code from instance_key: {instance_key}")
                continue

            cur.execute(
                """
                INSERT INTO courses (instance_key, course_code, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (instance_key) DO NOTHING;
                """,
                (
                    instance_key,
                    course_code,
                    json.dumps(course_data)
                )
            )
        print("Course data migration complete.")

        conn.commit()
        cur.close()
        conn.close()
        print("Data migration successful.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    migrate_data()
