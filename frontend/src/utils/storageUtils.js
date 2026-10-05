import { asResult } from './resultTypes';

const STORAGE_KEY = 'jhuCourseSearchHistory';
const PERCENTILE_PREFERENCE_KEY = 'jhuCourseShowPercentiles';
const PERCENTILE_WEIGHTING_KEY = 'jhuCourseWeightPercentilesByClassSize';
const MAX_HISTORY_ITEMS = 1000;

export const getShowPercentilesPreference = () => {
  try {
    return localStorage.getItem(PERCENTILE_PREFERENCE_KEY) === 'true';
  } catch {
    return false;
  }
};

export const saveShowPercentilesPreference = (enabled) => {
  try {
    localStorage.setItem(PERCENTILE_PREFERENCE_KEY, String(enabled));
  } catch (error) {
    console.warn('Failed to save percentile preference:', error);
  }
};

export const getPercentileWeightingPreference = () => {
  try {
    return localStorage.getItem(PERCENTILE_WEIGHTING_KEY) === 'true';
  } catch {
    return false;
  }
};

export const savePercentileWeightingPreference = (enabled) => {
  try {
    localStorage.setItem(PERCENTILE_WEIGHTING_KEY, String(enabled));
  } catch (error) {
    console.warn('Failed to save percentile weighting preference:', error);
  }
};

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
  const entry = { id: result.id, type: result.type, name, ...(result.type === 'course' ? { code: result.code } : {}) };
  save([entry, ...getSearchHistory().filter(item => item.id !== result.id)].slice(0, MAX_HISTORY_ITEMS));
};

export const removeFromSearchHistory = (selection) => {
  const id = typeof selection === 'string' && /^(course|professor):/.test(selection) ? selection : asResult(selection).id;
  save(getSearchHistory().filter(item => item.id !== id));
};

export const clearSearchHistory = () => save([]);
