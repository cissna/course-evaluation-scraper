import React, { useState, useEffect, useMemo, useRef } from 'react';
import './SearchHistory.css';
import { getSearchHistory, clearSearchHistory, removeFromSearchHistory } from '../utils/storageUtils';
import { filterSearchHistory } from '../utils/resultTypes';

const SearchHistory = ({ isOpen, onClose, onItemClick, onCompare, hasResults, atComparisonLimit, searchValue, currentResultId, anchorRef }) => {
  const [history, setHistory] = useState(getSearchHistory);
  const [displayCount, setDisplayCount] = useState(3);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const filtered = useMemo(() => filterSearchHistory(history, searchValue, currentResultId), [history, searchValue, currentResultId]);
  const visibleItems = filtered.slice(0, displayCount);

  useEffect(() => {
    const refresh = () => setHistory(getSearchHistory());
    window.addEventListener('storage', refresh);
    window.addEventListener('search-history-changed', refresh);
    return () => {
      window.removeEventListener('storage', refresh);
      window.removeEventListener('search-history-changed', refresh);
    };
  }, []);
  useEffect(() => {
    if (isOpen) { setHistory(getSearchHistory()); setDisplayCount(3); }
    setSelectedIndex(-1);
  }, [isOpen, searchValue]);
  useEffect(() => {
    const keydown = event => {
      if (!isOpen || event.target !== anchorRef.current) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        setSelectedIndex(previous => event.key === 'ArrowDown' ? Math.min(previous + 1, visibleItems.length - 1) : Math.max(previous - 1, -1));
      } else if (event.key === 'Enter' && visibleItems[selectedIndex]) {
        event.preventDefault();
        event.stopImmediatePropagation();
        onItemClick(visibleItems[selectedIndex]);
      } else if (event.key === 'Escape') {
        event.preventDefault(); onClose();
      }
    };
    const outside = event => {
      if (isOpen && !dropdownRef.current?.contains(event.target) && !anchorRef.current?.contains(event.target)) onClose();
    };
    document.addEventListener('keydown', keydown, true);
    document.addEventListener('mousedown', outside);
    return () => {
      document.removeEventListener('keydown', keydown, true);
      document.removeEventListener('mousedown', outside);
    };
  }, [isOpen, selectedIndex, visibleItems, onItemClick, onClose, anchorRef]);

  if (!isOpen || !filtered.length) return null;
  return (
    <div className="search-history-dropdown" ref={dropdownRef}>
      <div className="search-history-header"><span className="search-history-title">Recent Searches</span></div>
      <button className="search-history-close" onClick={onClose} aria-label="Close search history">×</button>
      <div className="search-history-list">
        {visibleItems.map((item, index) => (
          <div key={item.id} className={`search-history-item ${index === selectedIndex ? 'selected' : ''}`}
            onClick={event => { if (!event.target.closest('button')) onItemClick(item); }} onMouseEnter={() => setSelectedIndex(index)}>
            <button className="search-history-open" onClick={event => { event.stopPropagation(); onItemClick(item); }}>
              <span className={`result-type result-type-${item.type}`}>{item.type === 'professor' ? 'Professor' : 'Course'}</span>
              {item.type === 'course' && <span className="search-history-item-code">{item.code}</span>}
              <span className="search-history-item-name">{item.name}</span>
            </button>
            {hasResults && <button className="search-history-compare" disabled={atComparisonLimit}
              title={atComparisonLimit ? 'Remove a course or professor to add another.' : `Add ${item.name} side-by-side`}
              onClick={event => { event.stopPropagation(); onCompare(item); }}>side-by-side</button>}
            <button className="search-history-item-remove" aria-label={`Remove ${item.name} from history`}
              onClick={event => { event.stopPropagation(); removeFromSearchHistory(item); }}>×</button>
          </div>
        ))}
      </div>
      <div className="search-history-footer">
        {filtered.length > displayCount && <button className="search-history-action" onClick={() => setDisplayCount(count => count + 5)}>Show more</button>}
        <button className="search-history-action" onClick={() => {
          if (window.confirm('Are you sure you want to clear all search history?')) { clearSearchHistory(); onClose(); }
        }}>Clear all</button>
      </div>
    </div>
  );
};
export default SearchHistory;
