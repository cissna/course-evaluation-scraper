**Implementation Details:**

1.  The effect runs whenever `searchQuery` or the memoized `fetchResults` function changes.
2.  It checks if `searchQuery` is a non-empty string.
3.  **State Reset:** Before fetching, it resets the component's state (`results`, `totalCount`, `currentPage`, `error`) to their initial values. This is crucial to provide a clean slate for the new search results and to ensure the loading indicator is displayed correctly for a new search, rather than showing stale data.
4.  It then calls `fetchResults` for page `1` with the new `searchQuery`.

## 6. Event Handlers

-   **`handleLoadMore()`**:
    -   Calculates the next page number (`currentPage + 1`).
    -   Calls `fetchResults` with the `nextPage` and the current `searchQuery` to fetch and append the next set of results.

-   **`handleCourseClick(result)`**:
    -   This function determines the correct course identifier to pass to the `onCourseSelect` callback.
    -   Some search results may be "grouped" courses, where multiple course codes are associated. In this case, the API returns a `primary_course` field that represents the main course that matched the search.
    -   The logic is: if `result.primary_course` exists, use it; otherwise, fall back to `result.course_code`.
    -   It then calls the `onCourseSelect` prop with this identifier.

## 7. Rendering Logic

The component's JSX is heavily conditional to reflect the current state (loading, error, no results, has results, etc.).

-   **Derived State:** Two variables are calculated on each render for UI logic:
    -   `currentResultCount`: The number of results currently displayed or being loaded (`currentPage * resultsPerPage`).
    -   `hasMore`: A boolean indicating if there are more results to load (`currentResultCount < totalCount`).

-   **Header:**
    -   A "Back to Search" button that triggers the `onBack` prop.
    -   An `<h2>` displaying the search query.
    -   A `<p>` with a note explaining that the search is limited to courses already in the database.
    -   A results count that only displays if `totalCount > 0`, showing `Showing {X} of {Y} results`.

-   **Error Message:** A `div` with the class `error-message` is rendered if the `error` state is not `null`.

-   **Results List (`<div className="results-list">`)**:
    -   **Initial Load:** If `isLoading` is true and `results.length` is 0, a "Loading results..." message is shown.
    -   **No Results:** If not loading and `results.length` is 0, a "No results found" message is shown.
    -   **Display Results:** If there are results, it maps over the `results` array.
        -   Each result is rendered in a `div` with class `result-item`.
        -   The `key` for each item is set to `course.primary_course` or `course.course_code` for a stable identity, with `index` as a final fallback.
        -   An `onClick` handler is attached to each item, calling `handleCourseClick`.
        -   The course code and name are displayed in separate `div`s.

-   **Pagination/Footer:**
    -   **Loading More:** If `isLoading` is true and there are already results on screen (`results.length > 0`), a "Loading more results..." message is shown below the list.
    -   **Show More Button:** If `hasMore` is true and not currently loading, a "Show More Results" button is rendered. The button's text includes the number of remaining results.
    -   **End of Results:** If `!hasMore` is true and there are results, an "All results displayed" message is shown.