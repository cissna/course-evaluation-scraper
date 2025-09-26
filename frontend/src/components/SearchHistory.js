import React, { useState, useEffect, useCallback } from 'react';
import { getSearchHistory, clearSearchHistory } from '../utils/searchHistory';
import './SearchHistory.css';

const SearchHistory = ({
  isOpen,
  onClose,
  onItemClick,
  searchValue,
  currentCourseCode,
  anchorRef
}) => {
  const [history, setHistory] = useState([]);
  const [displayCount, setDisplayCount] = useState(3);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // Load history when component mounts or isOpen changes
  useEffect(() => {
    if (isOpen) {
      const storedHistory = getSearchHistory();
      setHistory(storedHistory);
      setDisplayCount(3); // Reset to initial count when opening
      setSelectedIndex(-1); // Reset selection
    }
  }, [isOpen]);

  // Get filtered history
  const getFilteredHistory = useCallback((historyList, searchVal, currentCode) => {
    // First exclude current course
    let filtered = historyList.filter(item => item.code !== currentCode);
    
    // Then apply search filter if there's a search value
    if (searchVal && searchVal.trim()) {
      const lowerSearch = searchVal.toLowerCase();
      filtered = filtered.filter(item => {
        const displayText = `${item.code} ${item.name}`.toLowerCase();
        return displayText.includes(lowerSearch);
      });
    }
    
    return filtered;
  }, []);

  // Filter history based on current search and current course code
  const filteredHistory = getFilteredHistory(history, searchValue, currentCourseCode);
  const visibleItems = filteredHistory.slice(0, displayCount);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      
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
  }, [isOpen, selectedIndex, visibleItems, onItemClick, onClose]);

  // Handle click outside to close dropdown
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event) => {
      if (anchorRef.current && !anchorRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose, anchorRef]);

  // Show more items
  const handleShowMore = () => {
    setDisplayCount(prev => prev + 5);
  };

  // Clear all history
  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all search history?')) {
      clearSearchHistory();
      setHistory([]);
      onClose();
    }
  };

  // Remove specific item from history
  const removeItem = (code) => {
    const updatedHistory = history.filter(item => item.code !== code);
    setHistory(updatedHistory);
    
    try {
      localStorage.setItem('jhuCourseSearchHistory', JSON.stringify({
        version: 1,
        items: updatedHistory
      }));
    } catch (e) {
      console.warn('Failed to update search history:', e);
    }
  };

  if (!isOpen || visibleItems.length === 0) {
    return null;
  }

  return (
    <div className="search-history-dropdown">
      <button className="search-history-close" onClick={onClose}>×</button>
      
      {visibleItems.map((item, index) => (
        <div 
          key={item.code}
          className={`search-history-item ${index === selectedIndex ? 'selected' : ''}`}
          onClick={() => onItemClick(item.code)}
        >
          <div className="search-history-item-content">
            <div className="search-history-course-code">{item.code}</div>
            <div className="search-history-course-name">{item.name}</div>
          </div>
          <button 
            className="search-history-item-remove"
            onClick={(e) => {
              e.stopPropagation();
              removeItem(item.code);
            }}
          >
            ×
          </button>
        </div>
      ))}
      
      {displayCount < filteredHistory.length && (
        <div className="search-history-actions">
          <button className="search-history-show-more" onClick={handleShowMore}>
            Show more
          </button>
          {displayCount > 3 && (
            <button className="search-history-clear-all" onClick={handleClearAll}>
              Clear all
            </button>
          )}
        </div>
      )}
      
      {displayCount >= filteredHistory.length && displayCount > 3 && (
        <div className="search-history-actions">
          <button className="search-history-clear-all" onClick={handleClearAll}>
            Clear all
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchHistory;