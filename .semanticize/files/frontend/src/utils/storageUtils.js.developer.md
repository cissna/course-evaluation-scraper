# Storage Utility Functions (`storageUtils.js`)

This module provides utility functions for managing the user's recent course search history stored in the browser's `localStorage`. It handles serialization, deserialization, modification, and maintenance of this history array.

The history is stored under the key `jhuCourseSearchHistory` and is limited to `MAX_HISTORY_ITEMS` (1000 entries). Each entry in the history is an object `{ code: string, name: string }`.

## High-Level Interaction Pattern

Components needing access to the history (e.g., displaying recent searches) should use `getSearchHistory`. Components performing a new search should call `addToSearchHistory` to record the action, which automatically handles deduplication and maintaining the size limit.

---

## Function Summaries

### `getSearchHistory()`

**Summary:** Retrieves the current list of recent course searches from `localStorage`.

**Details:**
* Reads the data stored under the application-specific key (`jhuCourseSearchHistory`).
* Safely parses the JSON data. If parsing fails or the data is missing, it returns an empty array (`[]`).
* Returns an array of history objects, where each object contains a course `code` and its displayed `name`.

### `addToSearchHistory(courseCode, courseName)`

**Summary:** Adds a new course search to the history, ensuring uniqueness and enforcing the maximum size limit.

**Details:**
* **Deduplication:** Before adding, it removes any existing entry matching the provided `courseCode`.
* **Name Normalization:** It attempts to determine a clean display name. If the provided `courseName` is null, empty, or matches the `courseCode`, it defaults the stored name to `'No data'`.
* **Insertion:** The new entry is added to the beginning of the history array (`unshift`) to represent the most recent search.
* **Limiting:** If the history size exceeds `MAX_HISTORY_ITEMS` (1000), the oldest entries are truncated (maintaining a FIFO structure based on insertion order).
* Saves the updated array back to `localStorage`.

### `removeFromSearchHistory(courseCode)`

**Summary:** Deletes a specific course entry from the search history based on its course code.

**Details:**
* Retrieves the current history.
* Filters out any entry whose `code` matches the provided `courseCode`.
* Saves the modified history back to `localStorage`.

### `clearSearchHistory()`

**Summary:** Completely removes the search history data from the browser's `localStorage`.

**Details:**
* Directly calls `localStorage.removeItem` using the defined storage key.