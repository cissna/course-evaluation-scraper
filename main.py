from workflow import run_scraper_workflow

if __name__ == "__main__":
    department_code = 'EN.601'
    # Loop through a reasonable range of course numbers for the department.
    # Using a range from 100 to 899 covers typical undergraduate and graduate courses.
    for course_number in range(0, 1000):
        # Format the course number to be three digits (e.g., 101, 220, 601)
        formatted_course_number = f"{course_number:03d}"
        target_course = f"{department_code}.{formatted_course_number}"
        
        print(f"--- Processing course: {target_course} ---")
        try:
            run_scraper_workflow(target_course)
            print(f"--- Finished processing: {target_course} ---\n")
        except Exception as e:
            # If an unexpected error occurs in the workflow for one course,
            # log it and continue to the next to ensure the script doesn't halt.
            print(f"--- CRITICAL ERROR in workflow for {target_course}: {e} ---")
            print("--- Moving to next course. ---\n")
            continue

    print("--- All department courses have been processed. ---")