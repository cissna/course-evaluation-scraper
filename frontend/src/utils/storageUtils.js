import { asResult } from './resultTypes';

const STORAGE_KEY = 'jhuCourseSearchHistory';
const MAX_HISTORY_ITEMS = 1000;

export const getSearchHistory = () => {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return Array.isArray(stored.items) ? stored.items.filter(item => item && (item.code || item.name)).map(asResult) : [];
  } catch {
    return [];
  }
};

const save = (items) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 2, items }));
    window.dispatchEvent(new Event('search-history-changed'));
  } catch (error) {
    console.warn('Failed to save search history:', error);
  }
};

export const addToSearchHistory = (selection, courseName) => {
  const result = asResult(selection);
  const name = result.type === 'professor' ? result.name : courseName || result.name || 'No data';
  save([{ ...result, name }, ...getSearchHistory().filter(item => item.id !== result.id)].slice(0, MAX_HISTORY_ITEMS));
};

export const removeFromSearchHistory = (selection) => {
  const id = typeof selection === 'string' && /^(course|professor):/.test(selection) ? selection : asResult(selection).id;
  save(getSearchHistory().filter(item => item.id !== id));
};

export const clearSearchHistory = () => save([]);
