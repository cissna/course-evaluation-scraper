The **Scraper Service** relies on the **Workflow Helpers** to execute the core, technical process of gathering data for a specific course.

Think of it this way:
1.  The **Scraper Service** acts as the primary coordinator. Its job is to decide *if* a course needs updating (checking cache, grace periods) and to handle external issues like authentication.
2.  When the Scraper Service determines that actual data retrieval is needed, it calls the function `scrape_course_data_core` which resides in the **Workflow Helpers** file.
3.  The **Workflow Helpers** file contains the complex, step-by-step engine (`scrape_course_data_core`) responsible for navigating the external website, collecting all necessary links (even handling complex pagination/section logic), scraping the actual evaluation details from those links, and updating the database with the findings.

In short, **Workflow Helpers provides the heavy-lifting, core data retrieval machinery that the Scraper Service orchestrates.**