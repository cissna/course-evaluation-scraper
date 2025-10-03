# Component: SearchResults

The `SearchResults` component is responsible for fetching, displaying, and paginating course search results based on a provided search query. It manages the loading state, error handling, and user interaction for viewing lists of courses returned from the backend API.

## Component Summary

This component acts as the primary view for displaying results after a search action has been initiated in a parent component. It fetches data incrementally (infinite scroll pattern) and presents results in a clickable list format.

### Key Responsibilities:
1.  **Data Fetching:** Calls the backend search endpoint (`/api/search/course_name_detailed/:query`) when the `searchQuery` prop changes, handling pagination via `limit` and `offset`.
2.  **State Management:** Tracks the list of `results`, the `totalCount`, the current `currentPage`, `isLoading` status, and potential `error` messages.
3.  **Pagination/Loading More:** Implements a "Load More" mechanism to fetch subsequent pages of results, appending them to the existing list.
4.  **User Interaction:** Renders results as clickable items that trigger the `onCourseSelect` callback with the appropriate course identifier.

### High-Level Interaction Patterns:

1.  **Initialization/Query Change:** When the `searchQuery` prop updates, the component resets its internal state (results, page, count) and triggers `fetchResults` for page 1.
2.  **Data Display:** Results are rendered sequentially. Loading indicators are shown when fetching the initial set or when loading more results.
3.  **Click Handling:** Clicking a result item invokes `handleCourseClick`, which determines the correct course identifier (handling potential grouping structure) and passes it up via `onCourseSelect`.
4.  **Load More:** When the user scrolls or explicitly clicks "Show More Results," `handleLoadMore` increments the page number and triggers another fetch, appending the new data.

---

## Hooks and Handlers Analysis

### State Variables:

| State | Type | Description |
| :--- | :--- | :--- |
| `results` | Array | Stores the currently loaded courses for display. |
| `totalCount` | Number | The total number of matching results available on the server. |
| `currentPage`| Number | The index of the page currently loaded (1-based). |
| `isLoading` | Boolean | Indicates if an API request is currently in progress. |
| `error` | String/Null | Stores any error message encountered during fetching. |

### Constants:

*   `resultsPerPage`: Fixed at `20`. Controls the batch size fetched in each API call.

### Functions:

#### `fetchResults(page, query)`
*   **Purpose:** Core function responsible for making the asynchronous API call to retrieve search results for a specific page and query.
*   **Mechanism:** Calculates the necessary `offset`, sets `isLoading` to true, executes the fetch request, and handles success or failure. On success, it merges new results if `page > 1` (for infinite scroll) or replaces them if `page === 1` (for a fresh search).
*   **Dependency:** Uses `useCallback` because it's referenced in `useEffect` and `handleLoadMore`.

#### `useEffect` (Dependency: `searchQuery`, `fetchResults`)
*   **Purpose:** Triggers the initial data fetching process whenever a new `searchQuery` is provided by the parent component.
*   **Mechanism:** Resets state variables (`results`, `totalCount`, `currentPage`) to default values before calling `fetchResults(1, searchQuery)` to ensure a clean search result view.

#### `handleLoadMore()`
*   **Purpose:** Called when the user requests to see the next batch of results.
*   **Mechanism:** Increments `currentPage` and calls `fetchResults` with the next page number.

#### `handleCourseClick(result)`
*   **Purpose:** Processes user selection of a displayed course item.
*   **Mechanism:** Determines the identifier to pass up: it prioritizes `result.primary_course` (suggesting grouped results) or falls back to `result.course_code`. It then calls the `onCourseSelect` prop function.

### Derived State:

*   `currentResultCount`: Calculates how many results are currently displayed based on `currentPage` and `resultsPerPage`.
*   `hasMore`: A boolean indicating if `currentResultCount` is less than `totalCount`, determining if the "Load More" button should be visible.