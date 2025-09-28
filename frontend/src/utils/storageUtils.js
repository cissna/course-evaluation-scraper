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

export const removeFromSearchHistory = (courseCode) => {
    try {
        let history = getSearchHistory();
        history = history.filter(item => item.code !== courseCode);
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
            version: 1,
            items: history
        }));
    } catch (e) {
        console.warn('Failed to remove from search history:', e);
    }
};

export const clearSearchHistory = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.warn('Failed to clear search history:', e);
  }
};
