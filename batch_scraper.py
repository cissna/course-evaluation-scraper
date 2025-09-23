#!/usr/bin/env python3
"""
Batch scraper for processing all courses from jhu_as_en_courses.txt
This script reuses the existing scraping logic without duplicating code.
"""

import os
import sys
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_helpers import scrape_course_data_core
from scraping_logic import get_authenticated_session
from data_manager import load_json_file, save_json_file
from config import METADATA_FILE, DATA_FILE


class BatchScraper:
    """Handles batch scraping of multiple courses with progress tracking and error handling."""
    
    def __init__(self, courses_file: str = "jhu_as_en_courses.txt", 
                 delay_between_courses: float = 1.0,
                 max_retries: int = 3):
        """
        Initialize the batch scraper.
        
        Args:
            courses_file: Path to file containing course codes
            delay_between_courses: Seconds to wait between scraping courses
            max_retries: Maximum retries for failed courses
        """
        self.courses_file = courses_file
        self.delay_between_courses = delay_between_courses
        self.max_retries = max_retries
        self.session = None
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'start_time': None,
            'end_time': None
        }
    
    def load_course_codes(self) -> List[str]:
        """Load course codes from the text file."""
        try:
            with open(self.courses_file, 'r') as f:
                course_codes = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(course_codes)} course codes from {self.courses_file}")
            return course_codes
        except FileNotFoundError:
            print(f"Error: Course file {self.courses_file} not found!")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading course file: {e}")
            sys.exit(1)
    
    def get_authenticated_session(self) -> bool:
        """Get authenticated session for scraping."""
        try:
            self.session = get_authenticated_session()
            print("✓ Authentication successful")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def check_course_already_scraped(self, course_code: str) -> bool:
        """Check if course has been recently scraped and is up-to-date."""
        metadata = load_json_file(METADATA_FILE)
        if course_code not in metadata:
            return False
        
        course_metadata = metadata[course_code]
        
        # Check if course has failed status
        if course_metadata.get('last_period_failed', False):
            return False
        
        # Check if course is up-to-date (simplified check)
        last_period = course_metadata.get('last_period_gathered')
        if last_period:
            # For batch processing, we'll re-scrape everything to ensure completeness
            # This could be made configurable in the future
            return False
        
        return True
    
    def scrape_single_course(self, course_code: str, retry_count: int = 0) -> Dict[str, Any]:
        """Scrape a single course with retry logic."""
        print(f"\n--- Processing course: {course_code} (attempt {retry_count + 1}/{self.max_retries + 1}) ---")
        
        try:
            # Use the core scraping function with grace period logic disabled for batch processing
            result = scrape_course_data_core(
                course_code=course_code,
                session=self.session,
                skip_grace_period_logic=True  # Skip grace period logic for batch processing
            )
            
            if result['success']:
                new_data_count = len([k for k in result['data'].keys() if k not in load_json_file(DATA_FILE)])
                print(f"✓ Successfully scraped {course_code} - Found {new_data_count} new data entries")
                return {
                    'course_code': course_code,
                    'success': True,
                    'new_data_count': new_data_count,
                    'total_data_count': len(result['data']),
                    'error': None
                }
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ Failed to scrape {course_code}: {error_msg}")
                return {
                    'course_code': course_code,
                    'success': False,
                    'new_data_count': 0,
                    'total_data_count': 0,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Exception during scraping: {str(e)}"
            print(f"✗ Exception scraping {course_code}: {error_msg}")
            return {
                'course_code': course_code,
                'success': False,
                'new_data_count': 0,
                'total_data_count': 0,
                'error': error_msg
            }
    
    def process_course_with_retry(self, course_code: str) -> Dict[str, Any]:
        """Process a single course with retry logic."""
        for attempt in range(self.max_retries + 1):
            result = self.scrape_single_course(course_code, attempt)
            
            if result['success']:
                return result
            
            # If not the last attempt, wait before retrying
            if attempt < self.max_retries:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        return result
    
    def save_progress_report(self, output_file: str = None):
        """Save a progress report to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"batch_scrape_report_{timestamp}.json"
        
        report = {
            'summary': {
                'total_courses': len(self.results['successful']) + len(self.results['failed']) + len(self.results['skipped']),
                'successful': len(self.results['successful']),
                'failed': len(self.results['failed']),
                'skipped': len(self.results['skipped']),
                'start_time': self.results['start_time'].isoformat() if self.results['start_time'] else None,
                'end_time': self.results['end_time'].isoformat() if self.results['end_time'] else None,
                'duration_seconds': (self.results['end_time'] - self.results['start_time']).total_seconds() if self.results['end_time'] and self.results['start_time'] else None
            },
            'successful_courses': self.results['successful'],
            'failed_courses': self.results['failed'],
            'skipped_courses': self.results['skipped']
        }
        
        save_json_file(output_file, report)
        print(f"\n📊 Progress report saved to: {output_file}")
        return output_file
    
    def run_batch_scraping(self, start_index: int = 0, max_courses: int = None, 
                          skip_existing: bool = False, dry_run: bool = False):
        """
        Run batch scraping for all courses.
        
        Args:
            start_index: Index to start from (for resuming)
            max_courses: Maximum number of courses to process (None for all)
            skip_existing: Skip courses that have been recently scraped
            dry_run: Only print what would be done without actually scraping
        """
        print("🚀 Starting batch scraping process...")
        self.results['start_time'] = datetime.now()
        
        # Load course codes
        course_codes = self.load_course_codes()
        
        # Apply limits
        if start_index > 0:
            course_codes = course_codes[start_index:]
            print(f"Starting from index {start_index}")
        
        if max_courses:
            course_codes = course_codes[:max_courses]
            print(f"Processing only {max_courses} courses")
        
        total_courses = len(course_codes)
        print(f"Total courses to process: {total_courses}")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No actual scraping will be performed")
            for i, course_code in enumerate(course_codes):
                print(f"  {i+1:4d}. {course_code}")
            return
        
        # Get authenticated session
        if not self.get_authenticated_session():
            print("❌ Cannot proceed without authentication")
            return
        
        # Process each course
        for i, course_code in enumerate(course_codes):
            print(f"\n{'='*60}")
            print(f"Progress: {i+1}/{total_courses} ({((i+1)/total_courses)*100:.1f}%)")
            print(f"{'='*60}")
            
            # Check if course should be skipped
            if skip_existing and self.check_course_already_scraped(course_code):
                print(f"⏭️  Skipping {course_code} (already up-to-date)")
                self.results['skipped'].append({
                    'course_code': course_code,
                    'reason': 'already_up_to_date'
                })
                continue
            
            # Process the course
            result = self.process_course_with_retry(course_code)
            
            # Categorize result
            if result['success']:
                self.results['successful'].append(result)
            else:
                self.results['failed'].append(result)
            
            # Add delay between courses to be respectful to the server
            if i < total_courses - 1:  # Don't delay after the last course
                print(f"⏳ Waiting {self.delay_between_courses} seconds before next course...")
                time.sleep(self.delay_between_courses)
        
        self.results['end_time'] = datetime.now()
        
        # Print summary
        self.print_summary()
        
        # Save progress report
        self.save_progress_report()
    
    def print_summary(self):
        """Print a summary of the batch scraping results."""
        total = len(self.results['successful']) + len(self.results['failed']) + len(self.results['skipped'])
        successful = len(self.results['successful'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        
        print(f"\n{'='*60}")
        print("📊 BATCH SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Total courses processed: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        
        if self.results['start_time'] and self.results['end_time']:
            duration = (self.results['end_time'] - self.results['start_time']).total_seconds()
            print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            if successful > 0:
                print(f"📈 Average time per successful course: {duration/successful:.1f} seconds")
        
        if failed > 0:
            print(f"\n❌ Failed courses:")
            for result in self.results['failed']:
                print(f"  - {result['course_code']}: {result['error']}")


def main():
    """Main entry point for the batch scraper."""
    parser = argparse.ArgumentParser(description='Batch scrape course evaluation data')
    parser.add_argument('--courses-file', default='jhu_as_en_courses.txt',
                       help='File containing course codes (default: jhu_as_en_courses.txt)')
    parser.add_argument('--start-index', type=int, default=0,
                       help='Index to start from (for resuming)')
    parser.add_argument('--max-courses', type=int, default=None,
                       help='Maximum number of courses to process')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip courses that are already up-to-date')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without actually scraping')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between courses in seconds (default: 1.0)')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retries for failed courses (default: 3)')
    
    args = parser.parse_args()
    
    # Create and run batch scraper
    scraper = BatchScraper(
        courses_file=args.courses_file,
        delay_between_courses=args.delay,
        max_retries=args.max_retries
    )
    
    scraper.run_batch_scraping(
        start_index=args.start_index,
        max_courses=args.max_courses,
        skip_existing=args.skip_existing,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()