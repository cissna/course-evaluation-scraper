import os
import psycopg2
from dotenv import load_dotenv

def clear_grace_period_flags():
    """
    Clears the last_scrape_during_grace_period flag for all courses in the database.
    This is useful when you want to reset all grace period warnings.
    """
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("DATABASE_URL environment variable not set.")
        return

    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # Get count of courses that currently have the flag set
        cur.execute("SELECT COUNT(*) FROM course_metadata WHERE last_scrape_during_grace_period IS NOT NULL")
        count_before = cur.fetchone()[0]

        print(f"Found {count_before} courses with grace period flags set.")

        # Clear the grace period flag for all courses
        cur.execute("UPDATE course_metadata SET last_scrape_during_grace_period = NULL WHERE last_scrape_during_grace_period IS NOT NULL")

        # Get count after update
        cur.execute("SELECT COUNT(*) FROM course_metadata WHERE last_scrape_during_grace_period IS NOT NULL")
        count_after = cur.fetchone()[0]

        conn.commit()

        print(f"Successfully cleared grace period flags. {count_before - count_after} courses updated.")
        print(f"Remaining courses with flags: {count_after}")

    except Exception as e:
        print(f"Error clearing grace period flags: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    clear_grace_period_flags()