# Product Requirements Document: Search History Feature

## 1. Overview

This document specifies the implementation of a search history feature for the JHU Course Evaluation Analyzer web application. The feature will store recently searched course codes locally and display them in a dropdown when users interact with the search textbox.

## 2. Technical Architecture

### 2.1 Storage Solution
- **Method**: localStorage (with graceful degradation if unavailable)
- **Key**: `jhuCourseSearchHistory`
- **Data Structure**:
```json
{
  "version": 1,
  "items": [
    {"code": "AS.180.101", "name": "Intro to Psychology"},
    {"code": "EN.601.220", "name": "Intermediate Programming"},
    {"code": "AS.171.101", "name": "No data"}
  ]
}
```
- **Size Limit**: Maximum 1000 items (FIFO removal when limit reached)
- **Persistence**: Indefinite until manually cleared

### 2.2 Component Structure
Create a new component `SearchHistory.js` that will be imported and used by `CourseSearch.js`.

```
frontend/src/components/
├── CourseSearch.js (modified)
├── SearchHistory.js (new)
└── SearchHistory.css (new)
```

## 3. Detailed Implementation

### 3.1 SearchHistory Component

```javascript
// SearchHistory.js structure
const SearchHistory = ({
  isOpen,
  onClose,
  onItemClick,
  searchValue,
  currentCourseCode,
  anchorRef
}) => {
  // Component implementation
};
```

### 3.2 Data Flow

1. **Adding to History**:
   - Intercept the successful response in `handleDataReceived` in `App.js`
   - Extract course code and name from `analysisResult.metadata.current_name`
   - Call history storage function with code and name
   - For "No data" cases, store with "No data" as the name

2. **Deduplication Logic**:
   - When storing a new item, remove all existing entries with the same course code
   - Add the new item to the beginning of the array
   - This ensures most recent search appears at top with updated name

3. **Current Course Exclusion**:
   - Pass `currentCourseCode` prop from `App.js` → `CourseSearch.js` → `SearchHistory.js`
   - Filter out items where `item.code === currentCourseCode` during rendering

### 3.3 Storage Implementation

```javascript
// Storage utility functions
const STORAGE_KEY = 'jhuCourseSearchHistory';
const MAX_HISTORY_ITEMS = 1000;

export const getSearchHistory = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    return parsed.items || [];
  } catch (e) {
    console.warn('Failed to read search history:', e);
    return [];
  }
};

export const addToSearchHistory = (courseCode, courseName) => {
  try {
    let history = getSearchHistory();
    
    // Remove any existing entries with this course code
    history = history.filter(item => item.code !== courseCode);
    
    // Determine the display name
    const displayName = (!courseName || 
                        courseName === courseCode || 
                        courseName === 'n/a' || 
                        courseName === 'na' || 
                        courseName === '') 
                        ? 'No data' 
                        : courseName;
    
    // Add to beginning
    history.unshift({ code: courseCode, name: displayName });
    
    // Enforce limit (FIFO)
    if (history.length > MAX_HISTORY_ITEMS) {
      history = history.slice(0, MAX_HISTORY_ITEMS);
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      version: 1,
      items: history
    }));
  } catch (e) {
    console.warn('Failed to save search history:', e);
  }
};

export const clearSearchHistory = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn('Failed to clear search history:', e);
  }
};
```

### 3.4 Dropdown Behavior

#### 3.4.1 Opening/Closing Logic
- **Open when**:
  - Search textbox is clicked (onFocus event)
  - Search textbox already has focus and is clicked again
  - Only if history has at least one item (excluding current course)

- **Close when**:
  - User clicks outside dropdown and search box
  - User presses Escape key
  - User clicks the close button
  - User clicks a history item
  - No items match the current filter

#### 3.4.2 Filtering
```javascript
const getFilteredHistory = (history, searchValue, currentCourseCode) => {
  // First exclude current course
  let filtered = history.filter(item => item.code !== currentCourseCode);
  
  // Then apply search filter if there's a search value
  if (searchValue && searchValue.trim()) {
    const lowerSearch = searchValue.toLowerCase();
    filtered = filtered.filter(item => {
      const displayText = `${item.code} ${item.name}`.toLowerCase();
      return displayText.includes(lowerSearch);
    });
  }
  
  return filtered;
};
```

#### 3.4.3 Display Logic
- Initially show 3 items
- "Show more" reveals 5 additional items per click
- "Show more" hidden when no more items to show
- "Clear all history" button appears next to "Show more" when expanded beyond 3 items

### 3.5 Integration Points

#### 3.5.1 Modify App.js
```javascript
// In handleDataReceived function, after setAnalysisResult(data):
if (data && !data.error) {
  setAnalysisResult(data);
  setAnalysisError(null);
  
  // Add to search history
  const courseName = data.metadata?.current_name || 'No data';
  addToSearchHistory(newCourseCode, courseName);
}

// For no data cases in the error handling:
if (response.status === 404 || data?.error === 'No data found for this course.') {
  // ... existing error handling ...
  addToSearchHistory(code, 'No data');
}
```

#### 3.5.2 Modify CourseSearch.js
```javascript
// Add new props and state
const CourseSearch = ({ onDataReceived, onLoadingChange, currentCourseCode }) => {
  const [showHistory, setShowHistory] = useState(false);
  const searchInputRef = useRef(null);
  
  // Handle history item click
  const handleHistoryItemClick = (courseCode) => {
    setQuery(courseCode);
    setShowHistory(false);
    onDataReceived(courseCode);
  };
  
  // Add SearchHistory component in render
  return (
    <div className="course-search">
      <input
        ref={searchInputRef}
        type="text"
        value={query}
        onFocus={() => setShowHistory(true)}
        onClick={() => setShowHistory(true)}
        // ... other props
      />
      <SearchHistory
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onItemClick={handleHistoryItemClick}
        searchValue={query}
        currentCourseCode={currentCourseCode}
        anchorRef={searchInputRef}
      />
      {/* ... rest of component */}
    </div>
  );
};
```

### 3.6 Visual Design Specifications

#### 3.6.1 Dropdown Container
```css
.search-history-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  max-height: none; /* No scrolling */
}
```

#### 3.6.2 Close Button
```css
.search-history-close {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-history-close:hover {
  background: #cc0000;
}
```

#### 3.6.3 History Items
```css
.search-history-item {
  padding: 8px 40px 8px 12px; /* Extra right padding for X button */
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
}

.search-history-item:hover,
.search-history-item.selected {
  background: #e3f2fd; /* Light blue */
}

.search-history-item-remove {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-history-item-remove:hover {
  background: #e0e0e0;
}
```

#### 3.6.4 Show More Link
```css
.search-history-show-more {
  color: #1976d2;
  text-decoration: underline;
  cursor: pointer;
  padding: 8px 12px;
  display: block;
}

.search-history-show-more:hover {
  color: #1565c0;
}
```

### 3.7 Keyboard Navigation

```javascript
// In SearchHistory component
const [selectedIndex, setSelectedIndex] = useState(-1);

useEffect(() => {
  const handleKeyDown = (e) => {
    if (!isOpen) return;
    
    const filteredItems = getFilteredHistory(history, searchValue, currentCourseCode);
    const visibleItems = filteredItems.slice(0, displayCount);
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < visibleItems.length - 1 ? prev + 1 : prev
        );
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > -1 ? prev - 1 : -1);
        break;
        
      case 'Enter':
        if (selectedIndex >= 0 && selectedIndex < visibleItems.length) {
          e.preventDefault();
          onItemClick(visibleItems[selectedIndex].code);
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  };
  
  document.addEventListener('keydown', handleKeyDown);
  return () => document.removeEventListener('keydown', handleKeyDown);
}, [isOpen, selectedIndex, history, searchValue, currentCourseCode, displayCount]);
```

### 3.8 Clear All Confirmation Dialog

```javascript
const handleClearAll = () => {
  if (window.confirm('Are you sure you want to clear all search history?')) {
    clearSearchHistory();
    setHistory([]);
    onClose();
  }
};
```

## 4. Edge Case Handling

### 4.1 Storage Disabled
- Wrap all localStorage calls in try-catch blocks
- Feature silently disabled if storage unavailable
- No error messages shown to user

### 4.2 Empty History
- Dropdown doesn't open if no items to show
- No visual change from current behavior

### 4.3 Viewport Overflow
- Let dropdown extend beyond viewport
- Browser will automatically add scrollbar to page
- No internal scrolling in dropdown

## 5. Testing Checklist

- [ ] History persists across page refreshes
- [ ] Current course never appears in its own history
- [ ] Clicking history item triggers search and fills textbox
- [ ] Deduplication works correctly
- [ ] FIFO removal at 1000 items
- [ ] Filtering works with partial matches
- [ ] Keyboard navigation works correctly
- [ ] "Show more" reveals exactly 5 items
- [ ] "Clear all" only appears when expanded
- [ ] Graceful degradation when localStorage disabled
- [ ] Close button, escape key, and outside clicks all close dropdown
- [ ] "No data" displayed for courses without evaluation data
