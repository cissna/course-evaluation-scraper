# App.js Technical Documentation

## 1. Overview

`App.js` is the root component of the React single-page application. It serves as the central controller, managing the application's overall state, orchestrating data flow between the backend API and child components, and controlling which view is displayed to the user. It handles all primary business logic, including fetching data, triggering client-side analysis, and managing user-configurable options like filters and data separation.

## 2. State Management

The component uses multiple `useState` hooks to manage its state:

-   **`analysisResult`**: Stores the output from the `analysisEngine.js`. This is the processed data that is ready for visualization by the `DataDisplay` component. It's `null` initially or when new data is being fetched.
-   **`rawCourseData`**: Caches the raw, unprocessed evaluation data fetched from the backend API (`/api/analyze/:code`). The structure is `{ courseCode: string, data: object }`. This cache is crucial for performance, as it allows the frontend to re-process data with new filters or statistics without making another network request.
-   **`courseCode`**: A string representing the currently selected course code (e.g., `AS.180.101`).
-   **`currentView`**: A string that determines which main component is rendered. It can be `'search'`, `'results'`, or `'analysis'`.
-   **`searchResultsQuery`**: Stores the user's search query string when a search yields multiple results, which is then passed to the `SearchResults` component.
-   **`advancedOptions`**: A complex state object that holds all user-configurable settings for data analysis. Its structure is:
    ```javascript
    {
      stats: { [statKey: string]: boolean }, // e.g., { 'mean': true, 'median': false }
      filters: { min_year: string, max_year: string, seasons: string[] },
      separationKeys: string[] // e.g., ['instructor', 'course_code']
    }
    ```
    It is initialized with default statistic selections from `STATISTICS_CONFIG`.
-   **`showLast3YearsActive`**: A boolean flag that tracks the state of the "Show Last 3 Years" toggle button. It is used to determine the button's text and behavior.
-   **`analysisError`**: Stores an error message string (can include HTML) to be displayed to the user, typically in the `DataDisplay` component.
-   **`loadingCount`**: An integer used as a reference counter for asynchronous operations. `startLoading` increments it, and `stopLoading` decrements it. The `isLoading` derived constant is true if `loadingCount > 0`, which robustly handles multiple concurrent loading states.
-   **`gracePeriodInfo`**: Stores the response from the `/api/grace-status/:code` endpoint, indicating if new evaluations for a course might be available but haven't been scraped yet.
-   **`dismissedGraceWarnings`**: A `Set` containing course codes for which the user has dismissed the grace period warning during the current session.

## 3. Core Functions & Data Flow

### 3.1. Data Fetching and Processing

#### `fetchAnalysisData(code, options, forceBackend = false)`

This is the primary function for fetching and processing course data.

-   **Parameters**:
    -   `code` (string): The course code to analyze.
    -   `options` (object): The `advancedOptions` object.
    -   `forceBackend` (boolean): If `true`, forces a refetch from the backend, bypassing the local cache.
-   **Client-Side Optimization**:
    1.  It first checks if `rawCourseData` exists for the requested `code` and if `forceBackend` is `false`.
    2.  If true, it avoids a network call and directly invokes `processAnalysisRequest` from `analysisEngine.js` with the cached raw data and new options. The result is stored in `analysisResult`.
    3.  If this local processing fails, it falls back to fetching from the backend.
-   **Backend Fetch Logic**:
    1.  Resets `analysisError` and `analysisResult`, and increments `loadingCount`.
    2.  Constructs a `params` object for the API request, which includes the `stats`, `filters`, and `separation_keys` from the `options`. Crucially, it adds `raw_data_mode: true` to instruct the backend to return the complete, unprocessed dataset.
    3.  Makes a `POST` request to `${API_BASE_URL}/api/analyze/${code}`.
    4.  **Response Handling**:
        -   **Success (2xx)**: The raw data from `data.raw_data` is cached in the `rawCourseData` state. It then immediately calls `processAnalysisRequest` to perform the initial client-side analysis. The result is stored in `analysisResult`, and the course is added to the search history via `addToSearchHistory`.
        -   **Not Found (404)**: Sets a specific `analysisError` message informing the user that no data was found and provides a direct, pre-filled link to the official JHU evaluation search page.
        -   **Other Errors**: Sets a generic `analysisError` message, including the error details from the API response, and asks the user to report the issue.
    5.  The `finally` block ensures `stopLoading()` is always called.

#### `checkGracePeriodStatus(code)`

-   **Parameters**: `code` (string)
-   **Functionality**: Asynchronously fetches the grace period status for a course from the `/api/grace-status/:code` endpoint and updates the `gracePeriodInfo` state.

#### `handleRecheck()`

-   **Functionality**: Allows the user to force a re-scrape of a course that is in a grace period.
    1.  Makes a `POST` request to `/api/recheck/:courseCode`.
    2.  On success, it adds the course code to `dismissedGraceWarnings`, invalidates the local cache by setting `rawCourseData` to `null`, and triggers a fresh data fetch by calling `fetchAnalysisData` with `forceBackend = true`.

### 3.2. Event Handlers

#### `handleDataReceived(newCourseCode)`

-   **Functionality**: Triggered when a user selects a single, specific course.
    1.  Updates `courseCode`, resets `rawCourseData`, and clears `dismissedGraceWarnings`.
    2.  Sets `currentView` to `'analysis'`.
    3.  **Important**: It explicitly removes `'course_name'` from the `separationKeys` in `advancedOptions`. This prevents a state where a previous separation setting could incorrectly affect the new course's data processing.
    4.  Initiates the data pipeline by calling `fetchAnalysisData` and `checkGracePeriodStatus`.

#### `handleApplyAdvancedOptions(options)`

-   **Functionality**: Triggered when any advanced option (stats, filters, separation) is changed.
    1.  Updates the `advancedOptions` state with the new `options`.
    2.  Performs basic validation on year filters.
    3.  Implements the same client-side optimization as `fetchAnalysisData`: if `rawCourseData` is available, it re-runs `processAnalysisRequest` locally. Otherwise, it calls `fetchAnalysisData` to get data from the backend.

#### `handleTimeFilterToggle()`, `handleSeparateByTeacherToggle()`, `handleSeparateByCourseCode()`

-   **Functionality**: These are toggle handlers. They update the `advancedOptions` state by adding or removing the relevant key (`min_year`/`max_year` for time, `'instructor'` or `'course_code'` for separation) and then immediately call `handleApplyAdvancedOptions` to re-process and display the data.

#### Other Handlers

-   **`handleMultipleResults(searchQuery)`**: Switches the view to `'results'`.
-   **`handleSearchResultSelect(courseCode)`**: A simple proxy to `handleDataReceived`.
-   **`handleBackToSearch()`**: Resets the application to its initial state.

## 4. Component Rendering (JSX)

The component's render method uses conditional rendering based on the `currentView` state.

-   **Header**: A static header with the application title.
-   **Main Content**:
    -   If `currentView` is `'search'` or `'analysis'`, the `CourseSearch` component is rendered to allow for new searches.
    -   If `currentView` is `'results'`, the `SearchResults` component is rendered.
    -   If `currentView` is `'analysis'`, it renders the full analysis view:
        -   **Course Title**: Displays the current course name and code from `analysisResult.metadata`. It also shows former names if they exist.
        -   **Grouping Info**: If the course is part of a group (`analysisResult.metadata.grouping_metadata.is_grouped`), a prominent box is displayed listing the other courses in the group and providing a button to toggle separation by `course_code`.
        -   **`GracePeriodWarning`**: Conditionally rendered if grace period information is available and the warning hasn't been dismissed.
        -   **Controls**: Buttons for toggling the "Last 3 Years" filter and "Separate by Professor".
        -   **`AdvancedOptions`**: The component that allows fine-grained control over statistics, filters, and separation.
        -   **`DataDisplay`**: The component responsible for rendering the tables of analyzed data. It receives the processed `analysisResult.data`, the list of selected stats, any error messages, and statistics metadata.
-   **Footer**: A static footer component.
-   **`LoadingOverlay`**: Rendered on top of all other content whenever `isLoading` is true.

This structure ensures that the UI is always in sync with the application's state, showing the appropriate components and data based on user actions.