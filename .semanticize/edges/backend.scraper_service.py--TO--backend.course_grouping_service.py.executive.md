The **Scraper Service** initiates an instance of the **Course Grouping Service** upon startup (`grouping_service = CourseGroupingService()`).

**Business Relationship:**

The Scraper Service is responsible for fetching the raw, up-to-date course data from external sources. However, to make this data meaningful and useful for users (e.g., ensuring that a search for one version of a course retrieves all equivalent versions), the Scraper Service relies on the Course Grouping Service.

The **Course Grouping Service** acts as the system's knowledge base for defining which course codes belong together (due to departmental equivalencies or explicit administrative groupings).

**Interaction Flow:**

While the Scraper Service doesn't appear to *call* the Grouping Service in the provided functions, its existence implies a dependency: the data fetched by the scraper is likely processed, stored, or queried later in a way that utilizes the grouping structure defined by the Course Grouping Service to maintain data consistency across related course offerings. In essence, the Scraper Service gathers the content, and the Grouping Service defines the structure/relationships of that content.