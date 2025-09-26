import React, { useState, useEffect, useRef } from 'react';
import {
  getSearchHistory,
  removeFromSearchHistory,
  clearSearchHistory
} from '../utils/searchHistory';
import './SearchHistory.css';

const INITIAL_DISPLAY_LIMIT = 3;
const SHOW_MORE_COUNT = 5;

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

const SearchHistory = ({
  isOpen,
  onClose,
  onItemClick,
  searchValue,
  currentCourseCode,
  anchorRef
}) => {
  const [history, setHistory] = useState([]);
  const [displayLimit, setDisplayLimit] = useState(INITIAL_DISPLAY_LIMIT);

  const dropdownRef = useRef();

  useEffect(() => {
    if (isOpen) {
      setDisplayLimit(INITIAL_DISPLAY_LIMIT);
      setHistory(getSearchHistory());
    }
  }, [isOpen]);

  const filteredHistory = getFilteredHistory(history, searchValue, currentCourseCode);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        (!anchorRef || !anchorRef.current || !anchorRef.current.contains(event.target))
      ) {
        onClose();
      }
    };
    const handleEsc = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen, onClose, anchorRef]);

  if (!isOpen || filteredHistory.length === 0) return null;

  const handleRemove = (code) => {
    removeFromSearchHistory(code);
    setHistory(getSearchHistory());
  };

  const handleClear = () => {
    clearSearchHistory();
    setHistory([]);
  };

  const canShowMore = filteredHistory.length > displayLimit;
  const visibleItems = filteredHistory.slice(0, displayLimit);

  return (
    <div className="search-history-dropdown" ref={dropdownRef}>
      <button
        className="search-history-close"
        aria-label="Close"
        onClick={onClose}
        title="Close history"
      >
        ×
      </button>
      {visibleItems.map(item => (
        <div
          key={item.code}
          className="search-history-item"
        >
          <div
            style={{ flex: 1 }}
            onClick={() => {
              onItemClick(item.code);
              onClose();
            }}
          >
            <span className="search-history-code">{item.code}</span>
            {" "}
            <span className="search-history-name">{item.name}</span>
          </div>
          <button
            className="search-history-item-remove"
            aria-label={`Remove ${item.code} from history`}
            title="Remove"
            onClick={() => handleRemove(item.code)}
          >
            ×
          </button>
        </div>
      ))}
      {canShowMore && (
        <span
          className="search-history-show-more"
          onClick={() => setDisplayLimit(displayLimit + SHOW_MORE_COUNT)}
        >
          Show more
        </span>
      )}
      {displayLimit > INITIAL_DISPLAY_LIMIT && (
        <button
          className="search-history-show-more"
          style={{ background: 'none', border: 'none' }}
          onClick={handleClear}
        >
          Clear all history
        </button>
      )}
    </div>
  );
};

export default SearchHistory;