import sys
import os
import time
import argparse
import requests
from datetime import datetime
from tqdm import tqdm

# Add the backend directory to the Python path to allow importing local db tools
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, backend_dir)

try:
    from backend.db_utils import get_db_connection
    from backend.period_logic import is_course_up_to_date, get_current_period
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    print("Make sure you are running this script from the one-time-scripts directory and your virtual environment is active.")
    sys.exit(1)

# API endpoint URL for forcing a scrape
BASE_URL = "https://course-evaluation-scraper.vercel.app/api/recheck/"

def tprint(*args, **kwargs):
    """Helper to print safely with tqdm"""
    tqdm.write(" ".join(map(str, args)), **kwargs)

class BatchScraper:
    def __init__(self, courses_file: str = "jhu_as_en_courses.txt", max_retries: int = 3, retry_failed: bool = False):
        self.courses_file = courses_file
        self.max_retries = max_retries
        self.retry_failed = retry_failed
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'start_time': None,
            'end_time': None
        }

    def load_course_codes(self) -> list:
        try:
            with open(self.courses_file, 'r') as f:
                course_codes = [line.strip() for line in f if line.strip()]
            tprint(f"Loaded {len(course_codes)} course codes from {self.courses_file}")
            return course_codes
        except FileNotFoundError:
            tprint(f"Error: Course file {self.courses_file} not found!")
            sys.exit(1)
        except Exception as e:
            tprint(f"Error reading course file: {e}")
            sys.exit(1)

    def fetch_all_metadata(self):
        tprint("📦 Fetching metadata cache directly from Supabase...")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM course_metadata")
                    rows = cur.fetchall()
                    colnames = [desc[0] for desc in cur.description]
                    tprint(f"✓ Cached {len(rows)} course metadata records locally.")
                    return {row[0]: dict(zip(colnames, row)) for row in rows}
        except Exception as e:
            tprint(f"Failed to fetch metadata from database: {e}")
            tprint("Falling back to making API requests for every course...")
            return None

    def scrape_single_course(self, course_code: str, retry_count: int = 0) -> dict:
        tprint(f"\n--- Scraping course via Vercel API: {course_code} (attempt {retry_count + 1}/{self.max_retries + 1}) ---")
        try:
            url = f"{BASE_URL}{course_code}"
            # Because we already pre-filtered using the database, any request we make here
            # genuinely needs to be scraped. So we use the POST recheck endpoint.
            response = requests.post(url, timeout=60)
            
            if response.status_code == 200:
                tprint(f"✓ Successfully scraped and updated {course_code}")
                return {'course_code': course_code, 'success': True, 'error': None, 'status': 200}
            elif response.status_code == 404:
                tprint(f"⏭️  Skipped {course_code}: No data found on JHU SIS")
                return {'course_code': course_code, 'success': False, 'error': 'No data found', 'status': 404}
            else:
                error_msg = f"HTTP Error {response.status_code}: {response.text}"
                tprint(f"✗ Failed to scrape {course_code}: {error_msg}")
                return {'course_code': course_code, 'success': False, 'error': error_msg, 'status': response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request exception: {str(e)}"
            tprint(f"✗ Exception scraping {course_code}: {error_msg}")
            return {'course_code': course_code, 'success': False, 'error': error_msg, 'status': None}
        except Exception as e:
            error_msg = f"Unexpected exception: {str(e)}"
            tprint(f"✗ Unexpected exception scraping {course_code}: {error_msg}")
            return {'course_code': course_code, 'success': False, 'error': error_msg, 'status': None}

    def process_course_with_retry(self, course_code: str) -> dict:
        for attempt in range(self.max_retries + 1):
            result = self.scrape_single_course(course_code, attempt)
            
            # If successful or it's a 404 (meaning we know there is definitely no data), don't retry
            if result['success'] or result.get('status') == 404:
                return result
                
            if attempt < self.max_retries:
                wait_time = (attempt + 1) * 2
                tprint(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        return result

    def run_batch_scraping(self, start_index: int = 0, max_courses: int = None, dry_run: bool = False):
        tprint("🚀 Starting ultra-fast batch scraping process...")
        self.results['start_time'] = datetime.now()
        
        course_codes = self.load_course_codes()
        
        if start_index > 0:
            course_codes = course_codes[start_index:]
            tprint(f"Starting from index {start_index}")
        
        if max_courses:
            course_codes = course_codes[:max_courses]
            tprint(f"Processing only {max_courses} courses")
        
        total_courses = len(course_codes)
        tprint(f"Total courses to process: {total_courses}")
        
        if dry_run:
            tprint("🔍 DRY RUN MODE - No actual API requests will be made")
            for i, course_code in enumerate(tqdm(course_codes, desc="Dry Run", unit="course")):
                pass
            return
            
        # 1. Fetch all metadata from Supabase in ONE query
        metadata_cache = self.fetch_all_metadata()
        current_period = get_current_period()
        tprint(f"Current evaluation period is: {current_period}")
        tprint("\n" + "="*60)
        
        for i, course_code in enumerate(tqdm(course_codes, desc="Processing Courses", unit="course", dynamic_ncols=True)):
            # 2. Local Cache Check
            if metadata_cache is not None:
                meta = metadata_cache.get(course_code)
                if meta:
                    # Check if it's a known failure (like a bad course code or persistent 500 error)
                    if meta.get('last_period_failed') and not self.retry_failed:
                        self.results['skipped'].append({'course_code': course_code, 'reason': 'known_failure'})
                        continue
                    
                    # Check if it's already completely up-to-date for the current semester
                    if is_course_up_to_date(meta.get('last_period_gathered'), meta):
                        self.results['skipped'].append({'course_code': course_code, 'reason': 'up_to_date'})
                        continue
            
            # 3. If we made it here, the course is either missing, outdated, or we are forcing retries.
            #    Hit the Vercel API to do the heavy lifting of scraping and inserting.
            result = self.process_course_with_retry(course_code)
            
            if result['success']:
                self.results['successful'].append(result)
            elif result.get('status') == 404:
                self.results['skipped'].append(result)
            else:
                self.results['failed'].append(result)
        
        self.results['end_time'] = datetime.now()
        self.print_summary()

    def print_summary(self):
        total = len(self.results['successful']) + len(self.results['failed']) + len(self.results['skipped'])
        successful = len(self.results['successful'])
        skipped = len(self.results['skipped'])
        failed = len(self.results['failed'])
        
        tprint(f"\n{'='*60}")
        tprint("📊 BATCH SCRAPING SUMMARY")
        tprint(f"{'='*60}")
        tprint(f"Total courses processed: {total}")
        tprint(f"✅ Newly Scraped & Updated: {successful}")
        tprint(f"⏭️  Skipped (Local Cache / No Data): {skipped}")
        tprint(f"❌ Failed: {failed}")
        
        if self.results['start_time'] and self.results['end_time']:
            duration = (self.results['end_time'] - self.results['start_time']).total_seconds()
            tprint(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        if failed > 0:
            tprint(f"\n❌ Failed courses:")
            for result in self.results['failed']:
                tprint(f"  - {result['course_code']}: {result['error']}")

def main():
    parser = argparse.ArgumentParser(description='Batch scrape course evaluation data via backend API')
    parser.add_argument('--courses-file', default='jhu_as_en_courses.txt', help='File containing course codes (default: jhu_as_en_courses.txt)')
    parser.add_argument('--start-index', type=int, default=0, help='Index to start from (for resuming)')
    parser.add_argument('--max-courses', type=int, default=None, help='Maximum number of courses to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without actually making requests')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retries for failed requests (default: 3)')
    parser.add_argument('--retry-failed', action='store_true', help='Force re-scrape of courses marked as last_period_failed=True in the database')
    
    args = parser.parse_args()
    
    scraper = BatchScraper(
        courses_file=args.courses_file,
        max_retries=args.max_retries,
        retry_failed=args.retry_failed
    )
    
    scraper.run_batch_scraping(
        start_index=args.start_index,
        max_courses=args.max_courses,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
