## `SearchHistory.js` Developer Documentation

### High-Level Summary

This file exports the `SearchHistory` React component, which is responsible for displaying a dropdown list of the user's recent course searches. The component is designed to appear below a search input field, providing a quick way for users to re-run previous queries.

The component manages its own state, retrieving search history from the browser's `localStorage` and handling user interactions like filtering, selection, and removal of history items. It is not responsible for fetching course data itself but rather for providing the selected course code back to a parent component.

### `SearchHistory` Component

#### **Component Overview**

The `SearchHistory` component is a stateful functional component that renders a dropdown menu of recent searches. It only renders when its `isOpen` prop is true and there are historical items to display. Its width is dynamically adjusted to match the search input it is anchored to.

#### **Interaction Patterns**

-   **Display**: The component becomes visible when the parent sets the `isOpen` prop to `true`. It automatically fetches the latest search history from `localStorage`.
-   **Filtering**: As the user types into the main search bar (communicated via the `searchValue` prop), the list of recent searches is filtered in real-time. The currently viewed course (via `currentCourseCode`) is always excluded from the list.
-   **Selection**: Users can select an item by:
    -   Clicking on it, which triggers the `onItemClick` callback.
    -   Using the `ArrowUp` and `ArrowDown` keys to navigate and `Enter` to select.
-   **Closing**: The dropdown can be closed by:
    -   The parent component setting `isOpen` to `false`.
    -   The user pressing the `Escape` key.
    -   The user clicking outside the component and its anchor element.
    -   The user clicking the close (`×`) button.
-   **History Management**:
    -   Users can remove a single item by clicking the `×` button next to it.
    -   Users can clear the entire search history via a "Clear all" button.
    -   The list automatically paginates, showing an initial set of items and a "Show more" button to expand the list.
-   **State Synchronization**: The component listens to the global `storage` event to automatically refresh its state if the search history is modified in another browser tab or window.

#### **Props**

-   `isOpen` (boolean): Controls the visibility of the dropdown.
-   `onClose` (function): A callback function to be executed when the component requests to be closed (e.g., on `Escape` key press or outside click).
-   `onItemClick` (function): A callback that is fired with the course code when a user selects an item from the history.
-   `searchValue` (string): The current text from the search input, used to filter the history results.
-   `currentCourseCode` (string): The code of the course currently being displayed, which is excluded from the history list.
-   `anchorRef` (React.RefObject): A ref pointing to the search input element. This is used to set the dropdown's width to match the input.

### Helper Functions

#### `getFilteredHistory(history, searchValue, currentCourseCode)`

A pure utility function that performs the logic of filtering the search history.

-   **Purpose**: Takes the complete search history array and returns a new array based on filtering criteria.
-   **Logic**:
    1.  It first removes any item whose code matches `currentCourseCode`.
    2.  If `searchValue` is present, it performs a case-insensitive search, keeping only items where the combined course code and name include the search term.
-   **Returns**: A filtered array of history items.