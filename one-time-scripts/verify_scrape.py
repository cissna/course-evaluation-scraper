import sys
import os
import requests

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, backend_dir)

from backend.scraping_logic import get_authenticated_session
from backend.scrape_search import get_evaluation_report_links
from backend.period_logic import get_current_period, get_year_from_period_string

def get_all_links_by_section(session, course_code):
    print(f"  [Fallback] Scanning section-by-section for {course_code}...")
    all_links = {}
    for i in range(100):
        section_code = f"{course_code}.{i:02d}"
        links, has_more = get_evaluation_report_links(session, section_code)
        if links:
            all_links.update(links)
    return all_links

def verify_course_completeness(course_code):
    print(f"\n🔍 VERIFYING: {course_code}")
    print("Authenticating with JHU SIS...")
    session = get_authenticated_session()
    
    print("Fetching initial report page...")
    initial_links, has_more_initial = get_evaluation_report_links(session, course_code)
    
    links_to_process = {}
    if not has_more_initial:
        print(f"  No pagination detected. Found {len(initial_links)} links.")
        links_to_process = initial_links
    else:
        print("  Pagination detected ('Show more results' button). Starting year-by-year scan from 2010...")
        links_to_process = initial_links.copy()
        
        current_year = get_year_from_period_string(get_current_period())
        switch_to_sections = False
        
        for year in range(2010, current_year + 2):
            yearly_links, has_more_yearly = get_evaluation_report_links(session, course_code, year=str(year))
            if has_more_yearly:
                print(f"  ⚠️ Year {year} STILL has pagination! JHU limits to 20 results per query. Switching to section-by-section scan.")
                switch_to_sections = True
                break
            if yearly_links:
                links_to_process.update(yearly_links)
                
        if switch_to_sections:
            section_links = get_all_links_by_section(session, course_code)
            links_to_process.update(section_links)
            
    print(f"\n✅ Total UNIQUE evaluations currently available on JHU SIS for {course_code}: {len(links_to_process)}")
    
    # Optional: List a few just to show it's real data
    print("\nSample of keys found directly on JHU:")
    sample_keys = sorted(list(links_to_process.keys()))[-5:]
    for key in sample_keys:
        print(f"  - {key}")

if __name__ == "__main__":
    verify_course_completeness("AS.171.103")
