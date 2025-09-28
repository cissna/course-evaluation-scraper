
import React, { useState, useEffect, useMemo, useRef } from 'react';
import './SearchHistory.css';
import { getSearchHistory, clearSearchHistory, removeFromSearchHistory } from '../utils/storageUtils';

const INITIAL_DISPLAY_COUNT = 3;
const SHOW_MORE_INCREMENT = 5;

const getFilteredHistory = (history, searchValue, currentCourseCode) => {
  let filtered = history.filter(item => item.code !== currentCourseCode);
  
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
  const [history, setHistory] = useState(getSearchHistory());
  const [displayCount, setDisplayCount] = useState(INITIAL_DISPLAY_COUNT);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [dropdownWidth, setDropdownWidth] = useState(0);
  const dropdownRef = useRef(null);

  const filteredHistory = useMemo(() => 
    getFilteredHistory(history, searchValue, currentCourseCode),
    [history, searchValue, currentCourseCode]
  );

  const visibleItems = useMemo(() => 
    filteredHistory.slice(0, displayCount),
    [filteredHistory, displayCount]
  );

  useEffect(() => {
    const handleRefresh = () => {
      setHistory(getSearchHistory());
    };
    window.addEventListener('storage', handleRefresh);
    return () => window.removeEventListener('storage', handleRefresh);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setHistory(getSearchHistory());
      setSelectedIndex(-1);
      setDisplayCount(INITIAL_DISPLAY_COUNT);
      if (anchorRef.current) {
        setDropdownWidth(anchorRef.current.offsetWidth);
      }
    }
  }, [isOpen, anchorRef]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, visibleItems.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, -1));
          break;
        case 'Enter':
          if (selectedIndex >= 0) {
            e.preventDefault();
            onItemClick(visibleItems[selectedIndex].code);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, visibleItems, onItemClick, onClose]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        isOpen &&
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        anchorRef.current &&
        !anchorRef.current.contains(event.target)
      ) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose, anchorRef]);

  const handleShowMore = () => {
    setDisplayCount(prev => prev + SHOW_MORE_INCREMENT);
  };

  const handleClearAll = () => {
    if (window.confirm('Are you sure you want to clear all search history?')) {
      clearSearchHistory();
      setHistory([]);
      onClose();
    }
  };

  const handleRemoveItem = (e, code) => {
    e.stopPropagation();
    removeFromSearchHistory(code);
    setHistory(getSearchHistory());
  };

  if (!isOpen || filteredHistory.length === 0) {
    return null;
  }

  return (
    <div 
      className="search-history-dropdown"
      ref={dropdownRef}
      style={{ width: dropdownWidth > 0 ? `${dropdownWidth}px` : 'auto' }}
    >
      <div className="search-history-header">
        <span className="search-history-title">Recent Searches</span>
        <button className="search-history-close" onClick={onClose}>&times;</button>
      </div>
      <div className="search-history-list">
        {visibleItems.map((item, index) => (
          <div
            key={item.code}
            className={`search-history-item ${index === selectedIndex ? 'selected' : ''}`}
            onClick={() => onItemClick(item.code)}
            onMouseEnter={() => setSelectedIndex(index)}
          >
            <span className="search-history-item-code">{item.code}</span>
            <span className="search-history-item-name">{item.name}</span>
            <button 
              className="search-history-item-remove"
              onClick={(e) => handleRemoveItem(e, item.code)}
            >
              &times;
            </button>
          </div>
        ))}
      </div>
      <div className="search-history-footer">
        {filteredHistory.length > displayCount && (
          <a href="#" className="search-history-action" onClick={handleShowMore}>
            Show more
          </a>
        )}
        {filteredHistory.length > 0 && (
           <a href="#" className="search-history-action" style={{marginLeft: 'auto'}} onClick={handleClearAll}>
            Clear all history
          </a>
        )}
      </div>
    </div>
  );
};

export default SearchHistory;
