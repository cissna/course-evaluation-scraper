## `CourseSearch` Component

The `CourseSearch` component provides the primary user interface for finding course evaluations. It renders a search input field and a search button, allowing users to search for courses by either their specific course code (e.g., `AS.180.101`) or by a general course name (e.g., "Introduction to Psychology").

### Core Functionality

-   **Dual Search Modes**: The component differentiates between two types of search queries:
    1.  **Course Code Search**: If the input matches a valid course code format, it directly triggers a data fetch for that specific course.
    2.  **Course Name Search**: If the input is not a course code, it performs a "detailed" search against the backend API (`/api/search/course_name_detailed/:query`).

-   **Result Handling**:
    -   If a name search returns a single unique course (or course group), it resolves to that course's primary code and passes it to the parent.
    -   If a name search returns multiple distinct course groups, it invokes the `onMultipleResults` callback, delegating the responsibility of displaying the results to a parent component (e.g., by navigating to a search results page).
    -   If no results are found, it displays an error message to the user.

-   **Search History Integration**: The component integrates with the `SearchHistory` component to display a dropdown of recently searched courses. This history is filtered in real-time as the user types and is anchored to the search input field.

### Props

-   `onDataReceived(courseCode)`: A callback function that is invoked when a single, definitive course code has been identified from the search. The parent component uses this to fetch and display the corresponding evaluation data.
-   `onMultipleResults(query)`: A callback function that is invoked when a search query yields multiple possible course groups. It passes the original search query to the parent, which is expected to handle the display of these ambiguous results.
-   `onLoadingChange(isLoading)`: A callback to notify the parent component of changes in the loading state, allowing the parent to display global loading indicators.
-   `currentCourseCode`: The course code for the data currently being viewed on the page. This is used to filter the current course out of the search history dropdown.

---

### `getFilteredHistory` Function

This is a helper function responsible for preparing the list of search history items to be displayed in the dropdown.

-   It takes the full search history, the user's current input (`searchValue`), and the `currentCourseCode` as arguments.
-   It filters out the course that is already being displayed on the page.
-   If the user has typed into the search box, it further filters the history to only include items that match the input, allowing for real-time filtering of the history dropdown.