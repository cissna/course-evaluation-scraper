from workflow import run_scraper_workflow

if __name__ == "__main__":
    # Example: Run the workflow for a specific course
    # This course code is from the project brief.
    target_course = 'AS.030.101'
    run_scraper_workflow(target_course)