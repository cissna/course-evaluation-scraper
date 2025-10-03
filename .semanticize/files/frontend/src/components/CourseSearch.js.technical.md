#### Parameters
-   `searchQuery` (String, optional): If provided (e.g., from a history click), this value is used as the search query. Otherwise, the function uses the `query` state.

#### Implementation Details
1.  **Query Validation**: It determines the final query to use and exits if the query is empty or just whitespace. It trims the query and truncates it to 1000 characters.
2.  **State Initialization**: It sets `isLoading` to `true`, clears any previous `error`, and hides the history dropdown (`setShowHistory(false)`).
3.  **Query Type Detection**: It uses a regular expression (`/^[A-Za-z]{2}\.\d{3}\.\d{3}$/`) to test if the `trimmedQuery` matches the format of a course code.
4.  **Execution Path (try...catch...finally)**:
    -   **If `isCourseCode` is `true`**:
        -   The `courseCode` is set to the uppercase version of the query.
        -   No API call is needed at this stage. The process jumps to the `onDataReceived` call.
    -   **If `isCourseCode` is `false` (a name search)**:
        -   It invokes `onLoadingChange(true)` to notify the parent.
        -   It makes a `fetch` request to the `/api/search/course_name_detailed/{query}` endpoint. This endpoint is designed to return grouped search results. A `limit=2` query parameter is used to efficiently check if there is more than one result group.
        -   **Response Handling**:
            -   If the response is not `ok`, it throws an error.
            -   If the parsed JSON `total_count` is `0`, it throws an error indicating no courses were found.
            -   If `total_count` is `1`, it means there's a single unambiguous result. It extracts the `primary_course` (or falls back to `course_code`) from the first result and sets this as the `courseCode`.
            -   If `total_count` is greater than `1`, the search is ambiguous. It calls the `onMultipleResults` prop with the original query, allowing the parent to handle it. The function then returns early. If `onMultipleResults` is not provided, it defaults to using the first result as a fallback.
5.  **Data Callback**: After a single `courseCode` has been determined (either directly or from a name search), it calls `onDataReceived(courseCode)`.
6.  **Error Handling (`catch`)**: If any error is thrown, it sets the `error` state with the error message and calls `onDataReceived(null)` to clear any existing data in the parent component.
7.  **Cleanup (`finally`)**: It always sets `isLoading` back to `false`. If the search was a name search, it also calls `onLoadingChange(false)`.

### Other Functions

-   `handleHistoryItemClick(courseCode)`: This function is passed to the `SearchHistory` component. When a user clicks a history item, it sets the `query` state to that item's `courseCode` and immediately calls `handleSearch` with that code.

### Rendering
-   The main container is a `div` with the class `course-search`.
-   The `<input>` field is controlled by the `query` state.
    -   `onKeyDown`: Triggers `handleSearch` on 'Enter' key press, but only if the query has changed.
    -   `onFocus` and `onClick`: Set `showHistory` to `true` to display the history dropdown.
    -   `className`: A special class `dropdown-visible` is added if the history dropdown is active, allowing for specific styling (e.g., changing the input's border-radius).
-   The `<SearchHistory>` component is rendered within the search container. It receives props to control its visibility (`isOpen`), handle closing (`onClose`), handle item clicks (`onItemClick`), and filter its content (`searchValue`, `currentCourseCode`). It also receives the `anchorRef` to position itself.
-   The `<button>` is disabled based on the `isLoading` state, and its text changes to "Searching..." during a search.
-   An error message paragraph is conditionally rendered if the `error` state is not null.