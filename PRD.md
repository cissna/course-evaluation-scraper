# Product Requirements Document: Search History Feature

## Overview
Add a search history dropdown to the course search input that appears when the user clicks the textbox. The history will store the 3 most recent searches (up to 1000 total) using cookies, allowing users to quickly revisit previously searched courses without re-entering queries.

## User Stories
- **As a student/researcher**, I want to quickly access recently searched courses so I can compare multiple course evaluations efficiently.
- **As a frequent user**, I want my search history to persist across browser sessions so I can continue where I left off.
- **As a mobile user**, I want an easy way to close the dropdown so I can navigate the page.
- **As a keyboard user**, I want to navigate history items with arrow keys and select them with Enter, just like Google search.

## Functional Requirements

### Core Functionality
1. **Dropdown Trigger**: History dropdown appears whenever the search textbox receives focus (onFocus event), regardless of whether text has been entered.
2. **History Storage**:
   - Store up to 1000 history items in browser cookies
   - Each item contains: course_code (uppercase), course_name, and timestamp
   - Cookies persist indefinitely until manually cleared
   - Use format: `course_history=[{"course_code":"AS.180.101","course_name":"Introduction to Psychology","timestamp":1703123456789},...]`
3. **History Display**:
   - Show 3 most recent items initially
   - "Show more" link appears if >3 items exist
   - Clicking "Show more" adds 5 more items and shows another "Show more" if more exist
   - Each item displays as: `{course_code} {course_name}`
4. **History Management**:
   - Add new searches to top of history after successful analysis (when `analysisResult` is set)
   - Move existing items to top when re-searched
   - Include failed searches with "No data" as course name
   - Update course names to most recent version using same logic as main display (`analysisResult.current_name`)
   - Individual "x" button next to each item to remove it
   - "Clear all history" button next to "Show more" link

### User Interactions
5. **Selection**: Clicking a history item fills the search box with the course_code and triggers search
6. **Closing**: Dropdown closes when user clicks outside the dropdown area or on the red "x" in top-right
7. **Keyboard Navigation**:
   - Arrow Down: Move selection down, fill search box with course_code, highlight item light blue
   - Arrow Up: Move selection up, restore original text if back at top
   - Enter: Select highlighted item and trigger search
   - Escape: Close dropdown and restore original search text

### UI/UX Requirements
8. **Dropdown Styling**:
   - Positioned flush below the search input, covering content below
   - Same width as search input (400px)
   - White background with subtle border matching input styling
   - Grows downward as more items are shown, potentially requiring page scroll
   - Red "x" button in top-right corner for mobile closure
9. **Item Styling**:
   - History items styled as plain text with hover effects
   - "Show more" styled as blue underlined link, not a button
   - Individual "x" buttons small and subtle next to each item
   - Highlighted item has light blue background
10. **Responsive Design**: Works on mobile with touch interactions

## Technical Requirements

### Frontend Components
1. **Modify CourseSearch.js**:
   - Add state: `showHistory`, `historyItems`, `selectedIndex`, `originalQuery`
   - Add event handlers: `onFocus`, `onBlur`, `onKeyDown` (extend existing)
   - Add useEffect for cookie loading on mount
   - Add functions: `loadHistory()`, `saveHistory()`, `updateHistory()`, `handleHistorySelect()`

2. **Create HistoryDropdown Component**:
   - Props: `items`, `onSelect`, `onRemove`, `onShowMore`, `onClearAll`, `onClose`
   - Render list items with course codes/names
   - Handle click events for selection/removal
   - Include "Show more" and "Clear all" controls

3. **Cookie Management**:
   - Use native `document.cookie` API
   - Functions: `getCookie()`, `setCookie()` with indefinite expiration
   - JSON parse/stringify for history array

### Backend Integration
4. **Course Name Updates**:
   - When loading history, call analysis API for each stored course_code to get current `current_name`
   - Update stored names in cookies after successful fetches
   - Handle API failures gracefully (keep old name or mark as "No data")

### Data Flow
5. **Search Flow**:
   - User searches → `handleSearch()` → `onDataReceived(courseCode)` → `fetchAnalysisData()` → success → `updateHistory(courseCode, current_name)`
   - History updated only after successful analysis result

### Implementation Details
6. **State Management**:
   - `historyItems`: Array of objects `{course_code, course_name, timestamp}`
   - `showHistory`: Boolean for dropdown visibility
   - `selectedIndex`: Number for keyboard navigation (-1 = none selected)

7. **Cookie Format**:
   ```javascript
   {
     course_code: "AS.180.101",
     course_name: "Introduction to Psychology",
     timestamp: 1703123456789
   }
   ```

8. **Edge Cases**:
   - Empty history: dropdown doesn't appear
   - Network failures during name updates: keep cached names
   - Course codes that no longer exist: still show in history, will show "no data" on search
   - Very long history: limit to 1000 items, remove oldest when exceeding
   - Mobile: ensure touch targets are adequate size

## Testing Criteria
- Dropdown appears on input focus
- 3 items shown initially, "Show more" adds 5 more
- Clicking items triggers search with correct course code
- Keyboard navigation works (arrows, enter, escape)
- Individual item removal works
- "Clear all" removes all history
- History persists across browser sessions
- Course names update to latest versions
- Failed searches included with "No data"
- Mobile close button works
- Clicking outside closes dropdown

## Implementation Notes
- No external libraries needed (use native cookies)
- Follow existing code patterns (state management, event handling)
- Maintain accessibility (ARIA labels, keyboard navigation)
- CSS should match existing component styling
- Add new CSS classes to CourseSearch.css
- Consider performance: batch name updates, limit concurrent API calls
- Error handling: failed cookie operations shouldn't break functionality