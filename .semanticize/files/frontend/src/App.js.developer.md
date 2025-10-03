## `App` Component

The `App` component is the root of the React application, acting as the central controller and state manager. It orchestrates the entire user experience, from searching for a course to displaying its analysis.

### High-Level Summary

-   **Role**: Manages the application's global state, including search results, analysis data, UI view, and user-selected options.
-   **Core Logic**: Contains the primary data fetching and processing logic. It fetches raw course data from the backend and then processes it for display. A key feature is its ability to perform client-side re-analysis of cached raw data when filters or display options change, minimizing backend calls.
-   **View Management**: Controls which of the three main views is active:
    1.  `search`: The initial view for finding courses.
    2.  `results`: Shown when a search query yields multiple possible courses.
    3.  `analysis`: The main view for displaying detailed course evaluation data.
-   **Interaction**: Renders child components (`CourseSearch`, `DataDisplay`, `AdvancedOptions`, etc.) and passes down state and event handler functions as props. It receives events from these children to trigger state updates, API calls, and view changes.

---

### Key Functions

#### `fetchAnalysisData(code, options, forceBackend = false)`

This is the core data-handling function. It's responsible for acquiring and processing the course evaluation data.

-   **Client-Side First**: It first checks if it already has the raw data for the requested `courseCode`. If so, and if a backend refetch isn't forced, it uses the `processAnalysisRequest` utility to re-run the analysis on the client with the new `options`. This makes filtering and changing display options nearly instantaneous.
-   **Backend Fallback**: If raw data is not available, is for a different course, or if `forceBackend` is true, it makes a `POST` request to the `/api/analyze/:course_code` endpoint.
-   **State Updates**: On a successful fetch, it updates two key state variables:
    -   `rawCourseData`: Stores the complete, unprocessed data from the backend. This is cached for future client-side processing.
    -   `analysisResult`: Stores the processed data ready for rendering by the `DataDisplay` component.
-   **Error Handling**: Manages API errors, including a specific 404 "No data found" case, and updates the `analysisError` state to provide user feedback.

#### `checkGracePeriodStatus(code)`

-   **Purpose**: Asynchronously calls the `/api/grace-status/:code` endpoint after a course is selected.
-   **Function**: Determines if the course is in a "grace period," where new evaluation data might be available but hasn't been scraped yet. The result is stored in `gracePeriodInfo` and used by the `GracePeriodWarning` component.

#### `handleRecheck()`

-   **Purpose**: Allows the user to manually trigger a re-scrape of a course that is in a grace period.
-   **Function**: Makes a `POST` request to `/api/recheck/:course_code`. On success, it invalidates the local `rawCourseData` and calls `fetchAnalysisData` to get the fresh data.

#### `handleDataReceived(newCourseCode)`

-   **Trigger**: Called when the `CourseSearch` component successfully identifies a single course to analyze.
-   **Function**: This is the primary entry point into the analysis view. It sets the `currentView` to 'analysis', resets relevant state (like grace period warnings), and triggers the initial `fetchAnalysisData` for the new course.

#### `handleMultipleResults(searchQuery)`

-   **Trigger**: Called by `CourseSearch` when a query returns multiple potential matches.
-   **Function**: Switches the `currentView` to 'results' and passes the `searchQuery` to the `SearchResults` component.

#### `handleApplyAdvancedOptions(options)`

-   **Trigger**: Called by the `AdvancedOptions` component or by shortcut buttons (e.g., "Separate by Professor") when the user changes any analysis parameter.
-   **Function**: Updates the `advancedOptions` state and then triggers a re-processing of the data by calling `fetchAnalysisData`. This typically results in a fast, client-side-only update if the raw data is already present.

#### State Management & Prop Drilling

The `App` component holds all major state variables (`analysisResult`, `rawCourseData`, `advancedOptions`, `isLoading`, etc.). It passes subsets of this state and corresponding handler functions down to child components as props. This follows a standard top-down data flow pattern where the `App` component is the single source of truth.