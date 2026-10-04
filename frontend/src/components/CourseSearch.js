import React, { useState, useRef } from 'react';
import './CourseSearch.css';
import { API_BASE_URL } from '../config';
import SearchHistory from './SearchHistory';
import { getSearchHistory } from '../utils/storageUtils';
import { asResult, filterSearchHistory, NO_RESULTS_MESSAGE } from '../utils/resultTypes';

const CourseSearch = ({ onDataReceived, onMultipleResults, currentResultId }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const searchInputRef = useRef(null);
  const requestRef = useRef(0);
  const filteredHistory = filterSearchHistory(getSearchHistory(), query, currentResultId);

  const handleSearch = async () => {
    const trimmedQuery = query.trim().slice(0, 1000);
    if (!trimmedQuery || isLoading) return;
    const request = ++requestRef.current;
    setIsLoading(true);
    setError(null);
    setShowHistory(false);
    try {
      if (/^[A-Za-z]{2}\.\d{3}\.\d{3}$/.test(trimmedQuery)) {
        onDataReceived(asResult(trimmedQuery.toUpperCase()));
        return;
      }
      const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(trimmedQuery)}&limit=20`);
      if (!response.ok) throw new Error('Error searching for course or professor name.');
      const matches = await response.json();
      if (request !== requestRef.current) return;
      const count = matches.courses.total_count + matches.professors.total_count;
      if (!count) throw new Error(NO_RESULTS_MESSAGE);
      if (count === 1) {
        const result = matches.courses.total_count ? matches.courses.results[0] : { ...matches.professors.results[0], type: 'professor' };
        onDataReceived(asResult(result));
      } else {
        onMultipleResults(trimmedQuery, matches);
      }
    } catch (err) {
      if (request === requestRef.current) setError(err.message);
    } finally {
      if (request === requestRef.current) setIsLoading(false);
    }
  };

  const handleHistoryItemClick = (result) => {
    ++requestRef.current;
    setIsLoading(false);
    setQuery(result.type === 'professor' ? result.name : result.code);
    setError(null);
    setShowHistory(false);
    onDataReceived(asResult(result));
  };

  return (
    <div className="course-search">
      <div className="search-controls">
        <div className="search-input-container">
          <input
            ref={searchInputRef} type="text" value={query} maxLength="1000"
            aria-label="Course code, course name, or professor name"
            className={showHistory && filteredHistory.length ? 'dropdown-visible' : undefined}
            onChange={event => setQuery(event.target.value)}
            onKeyDown={event => { if (event.key === 'Enter' && !event.defaultPrevented) handleSearch(); }}
            onFocus={() => setShowHistory(true)} onClick={() => setShowHistory(true)}
            placeholder="Enter course code, course name, or professor name"
          />
          <SearchHistory isOpen={showHistory} onClose={() => setShowHistory(false)} onItemClick={handleHistoryItemClick}
            searchValue={query} currentResultId={currentResultId} anchorRef={searchInputRef} />
        </div>
        <button onClick={handleSearch} disabled={isLoading}>{isLoading ? 'Searching...' : 'Search'}</button>
      </div>
      {error && <p className="error-message" role="alert">{error}</p>}
    </div>
  );
};

export default CourseSearch;
