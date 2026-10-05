import React, { useState, useRef } from 'react';
import './CourseSearch.css';
import { API_BASE_URL } from '../config';
import SearchHistory from './SearchHistory';
import { getSearchHistory } from '../utils/storageUtils';
import { asResult, filterSearchHistory, NO_RESULTS_MESSAGE } from '../utils/resultTypes';

const CourseSearch = ({ onDataReceived, onMultipleResults, currentResultId, hasResults, atComparisonLimit, resolving, searchError, onSearchStart }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const searchInputRef = useRef(null);
  const requestRef = useRef(0);
  const filteredHistory = filterSearchHistory(getSearchHistory(), query, currentResultId);

  const handleSearch = async (intent = 'replace') => {
    const trimmedQuery = query.trim().slice(0, 1000);
    if (!trimmedQuery || isLoading || (intent === 'add' && atComparisonLimit)) return;
    const request = ++requestRef.current;
    setIsLoading(true);
    setError(null);
    onSearchStart();
    setShowHistory(false);
    try {
      if (/^[A-Za-z]{2}\.\d{3}\.\d{3}$/.test(trimmedQuery)) {
        await onDataReceived(asResult(trimmedQuery.toUpperCase()), intent);
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
        await onDataReceived(asResult(result), intent);
      } else {
        onMultipleResults(trimmedQuery, matches, intent);
      }
    } catch (err) {
      if (request === requestRef.current) setError(err.message);
    } finally {
      if (request === requestRef.current) setIsLoading(false);
    }
  };

  const handleHistoryItemClick = (result, intent = 'replace') => {
    ++requestRef.current;
    setIsLoading(false);
    setQuery(result.type === 'professor' ? result.name : result.code);
    setError(null);
    setShowHistory(false);
    onDataReceived(asResult(result), intent);
  };

  return (
    <div className="course-search">
      <div className={`search-controls${hasResults ? ' with-comparison' : ''}`}>
        <div className="search-primary-controls">
        <div className="search-input-container">
          <input
            ref={searchInputRef} type="text" value={query} maxLength="1000"
            aria-label="Course code, course name, or professor name"
            className={showHistory && filteredHistory.length ? 'dropdown-visible' : undefined}
            onChange={event => setQuery(event.target.value)}
            onKeyDown={event => { if (event.key === 'Enter' && !event.defaultPrevented) handleSearch('replace'); }}
            onFocus={() => setShowHistory(true)} onClick={() => setShowHistory(true)}
            placeholder="Enter course code, course name, or professor name"
          />
          <SearchHistory isOpen={showHistory} onClose={() => setShowHistory(false)} onItemClick={handleHistoryItemClick}
            onCompare={result => handleHistoryItemClick(result, 'add')} atComparisonLimit={atComparisonLimit}
            searchValue={query} currentResultId={currentResultId} anchorRef={searchInputRef} />
        </div>
        <button onClick={() => handleSearch('replace')} disabled={isLoading || resolving}>{isLoading || resolving ? 'Searching...' : 'Search'}</button>
        {hasResults && <button className="add-comparison-button" onClick={() => handleSearch('add')} disabled={isLoading || resolving || atComparisonLimit}
          title={atComparisonLimit ? 'Remove a course or professor to add another.' : undefined}>Add side-by-side</button>}
        </div>
      </div>
      {(error || searchError) && <p className="error-message" role="alert">{error || searchError}</p>}
      {atComparisonLimit && <p className="comparison-limit" role="status">Remove a course or professor to add another.</p>}
    </div>
  );
};

export default CourseSearch;
