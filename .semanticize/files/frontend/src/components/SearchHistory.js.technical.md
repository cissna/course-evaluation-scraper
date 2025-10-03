### Technical Documentation for `SearchHistory.js`

#### Overview

`SearchHistory.js` implements a React functional component that renders a dropdown menu displaying the user's recent course searches. This component is designed to be highly interactive, supporting keyboard navigation, filtering, and direct management of the search history (removing items, clearing all). It retrieves and persists search history data using the browser's `localStorage` via utility functions.

---

#### Constants

-   **`INITIAL_DISPLAY_COUNT`**: A constant integer set to `3`. It defines the number of search history items to display initially when the dropdown is opened.
-   **`SHOW_MORE_INCREMENT`**: A constant integer set to `5`. It defines how many additional items are revealed each time the "Show more" button is clicked.

---

#### Helper Function: `getFilteredHistory`

This is a pure function responsible for filtering the search history list based on several criteria.

-   **Signature**: `getFilteredHistory(history, searchValue, currentCourseCode)`
-   **Parameters**:
    -   `history` (Array): An array of search history item objects, where each object is expected to have `code` and `name` properties.
    -   `searchValue` (string): The current text entered by the user in the search input field.
    -   `currentCourseCode` (string): The course code of the currently displayed course page.
-   **Returns**: A new array containing the filtered and sorted list of history items.
-   **Algorithm**:
    1.  It first filters the `history` array to exclude any item whose `code` matches the `currentCourseCode`. This prevents showing a link to the page the user is already on.
    2.  It then checks if `searchValue` is a non-empty string.
    3.  If `searchValue` exists, it performs a second filter operation. For each history item, it creates a concatenated string `${item.code} ${item.name}`, converts it to lower case, and checks if it `includes()` the lower-cased `searchValue`. This allows users to filter their history in real-time.
    4.  The final filtered array is returned.

---

#### Component: `SearchHistory`

This is the main React component.

-   **Signature**: `SearchHistory({ isOpen, onClose, onItemClick, searchValue, currentCourseCode, anchorRef })`
-   **Props**:
    -   `isOpen` (boolean): Controls the visibility of the dropdown. If `true`, the component attempts to render; otherwise, it renders `null`.
    -   `onClose` (function): A callback function to be executed when the dropdown should be closed (e.g., by pressing 'Escape' or clicking outside).
    -   `onItemClick` (function): A callback function executed when a user clicks on a history item. It receives the `item.code` as an argument.
    -   `searchValue` (string): The current value from the main search input, used to filter the history.
    -   `currentCourseCode` (string): The code of the course currently being viewed, passed to `getFilteredHistory`.
    -   `anchorRef` (React.RefObject): A ref object pointing to the search input element. This is used to position the dropdown and match its width.
-   **State**:
    -   `history` (Array): Stores the list of search history items. Initialized by calling `getSearchHistory()` from `storageUtils`.
    -   `displayCount` (number): Tracks the number of items to be shown from the history list. Initialized to `INITIAL_DISPLAY_COUNT`.
    -   `selectedIndex` (number): The index of the currently highlighted item for keyboard navigation. Initialized to `-1` (no selection).
    -   `dropdownWidth` (number): The calculated width in pixels for the dropdown, designed to match the width of the `anchorRef` element. Initialized to `0`.
-   **Refs**:
    -   `dropdownRef` (React.RefObject): A ref attached to the main `div` of the dropdown to detect clicks outside of it.

#### Hooks and Logic

-   **`useMemo` for `filteredHistory`**:
    -   Memoizes the result of the `getFilteredHistory` function.
    -   The function re-computes only if `history`, `searchValue`, or `currentCourseCode` props/state change. This is a performance optimization to avoid re-filtering on every render.

-   **`useMemo` for `visibleItems`**:
    -   Memoizes a sliced version of `filteredHistory` using `displayCount`.
    -   This creates the list of items that are actually rendered. It re-computes only if `filteredHistory` or `displayCount` change.

-   **`useEffect` for Storage Events**:
    -   **Trigger**: Runs once on component mount (`[]`).
    -   **Logic**: It adds a `storage` event listener to the `window` object. This allows the component to automatically refresh its `history` state by calling `getSearchHistory()` if the `localStorage` is modified by another browser tab or window.
    -   **Cleanup**: Removes the event listener when the component unmounts.

-   **`useEffect` for Opening the Dropdown**:
    -   **Trigger**: Runs whenever the `isOpen` prop changes.
    -   **Logic**: When `isOpen` becomes `true`, it performs several setup actions:
        1.  Refreshes the `history` state from `localStorage`.
        2.  Resets `selectedIndex` to `-1`.
        3.  Resets `displayCount` to `INITIAL_DISPLAY_COUNT`.
        4.  Measures the width of the `anchorRef.current` element and updates the `dropdownWidth` state, ensuring the dropdown matches the input field's width.

-   **`useEffect` for Keyboard Navigation**:
    -   **Trigger**: Runs when `isOpen`, `selectedIndex`, `visibleItems`, `onItemClick`, or `onClose` change.
    -   **Logic**: Adds a `keydown` event listener to the `document`. It only acts if `isOpen` is true.
        -   `ArrowDown`: Prevents default browser action, increments `selectedIndex`, clamping it to the last item's index.
        -   `ArrowUp`: Prevents default, decrements `selectedIndex`, clamping it to `-1`.
        -   `Enter`: If an item is selected (`selectedIndex >= 0`), it prevents default and calls `onItemClick` with the selected item's code.
        -   `Escape`: Prevents default and calls `onClose`.
    -   **Cleanup**: Removes the `keydown` listener.

-   **`useEffect` for "Click Outside" Logic**:
    -   **Trigger**: Runs when `isOpen`, `onClose`, or `anchorRef` change.
    -   **Logic**: Adds a `mousedown` event listener to the `document`. It checks if a click occurred outside of both the dropdown itself (`dropdownRef`) and the element that anchors it (`anchorRef`). If so, it calls `onClose`.
    -   **Cleanup**: Removes the `mousedown` listener.

#### Event Handlers

-   **`handleShowMore()`**: Increments the `displayCount` state by `SHOW_MORE_INCREMENT`.
-   **`handleClearAll()`**:
    1.  Shows a `window.confirm` dialog to the user.
    2.  If confirmed, it calls `clearSearchHistory()` to wipe the data from `localStorage`.
    3.  It updates the local `history` state to an empty array `[]`.
    4.  Calls `onClose()` to close the dropdown.
-   **`handleRemoveItem(e, code)`**:
    1.  Calls `e.stopPropagation()` to prevent the `onClick` on the parent `div` (the history item itself) from firing.
    2.  Calls `removeFromSearchHistory(code)` to remove the specific item from `localStorage`.
    3.  Refreshes the local `history` state by calling `getSearchHistory()`.

#### Rendering

-   The component returns `null` (renders nothing) if `!isOpen` or if `filteredHistory` is empty.
-   **Main Container (`div.search-history-dropdown`)**:
    -   Styled with a dynamic `width` from the `dropdownWidth` state.
    -   Attached to `dropdownRef`.
-   **Header**: Contains a title (`Recent Searches`) and a close button (`&times;`).
-   **List (`div.search-history-list`)**:
    -   Maps over `visibleItems` to render each history item.
    -   Each item is a `div` with a unique `key` (`item.code`).
    -   A `selected` class is conditionally applied if its `index` matches `selectedIndex`.
    -   `onClick`: Triggers `onItemClick` with the item's code.
    -   `onMouseEnter`: Updates `selectedIndex` to the item's index, allowing for mouse-over highlighting.
    -   Inside each item, the course code and name are displayed in separate `<span>` elements.
    -   A remove button (`&times;`) is included with an `onClick` handler bound to `handleRemoveItem`.
-   **Footer**:
    -   Conditionally renders a "Show more" button if there are more items in `filteredHistory` than are currently displayed (`displayCount`).
    -   Conditionally renders a "Clear all history" button if the history is not empty.

---