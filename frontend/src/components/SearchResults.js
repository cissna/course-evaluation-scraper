import React, { useState, useEffect, useRef } from 'react';
import './SearchResults.css';
import { API_BASE_URL } from '../config';
import { asResult } from '../utils/resultTypes';

export function comparisonSearchHeading(matches) {
  const courses = matches.courses.total_count > 0, professors = matches.professors.total_count > 0;
  return `Choose a ${courses && professors ? 'course or professor' : courses ? 'course' : 'professor'} to add side-by-side`;
}

const SearchResults = ({ searchQuery, initialResults, onResultSelect, onBack, intent = 'replace', resolving }) => {
  const [matches, setMatches] = useState(initialResults);
  const [activeTab, setActiveTab] = useState(initialResults.courses.total_count ? 'courses' : 'professors');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const controller = useRef(null);
  useEffect(() => () => controller.current?.abort(), []);
  const active = matches[activeTab];

  const loadMore = async () => {
    setIsLoading(true); setError(null);
    controller.current = new AbortController();
    try {
      const offsetKey = activeTab === 'courses' ? 'course_offset' : 'professor_offset';
      const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(searchQuery)}&limit=20&${offsetKey}=${active.results.length}`, { signal: controller.current.signal });
      if (!response.ok) throw new Error('Failed to fetch search results.');
      const next = await response.json();
      setMatches(previous => ({ ...previous, [activeTab]: { ...next[activeTab], results: [...previous[activeTab].results, ...next[activeTab].results] } }));
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message);
    } finally { setIsLoading(false); }
  };

  return (
    <div className="search-results">
      <div className="search-results-header">
        <button onClick={onBack} className="back-button">← Back to Search</button>
        <h2>{intent === 'add' ? comparisonSearchHeading(matches) : `Search Results for "${searchQuery}"`}</h2>
        <p className="search-note">Search includes courses with saved evaluations. If a course is missing, enter its full code (e.g., AS.180.101) to look it up.</p>
        <div className="search-tabs" role="tablist" aria-label="Result types">
          {['courses', 'professors'].map(type => (
            <button key={type} role="tab" aria-selected={activeTab === type} disabled={!matches[type].total_count || isLoading}
              className={`search-tab result-type-${type === 'courses' ? 'course' : 'professor'}`}
              onClick={() => setActiveTab(type)}>{type === 'courses' ? 'Courses' : 'Professors'} ({matches[type].total_count})</button>
          ))}
        </div>
        <p className="results-count">Showing {active.results.length} of {active.total_count} results</p>
      </div>
      {error && <div className="error-message" role="alert">{error}</div>}
      <div className="results-list" role="tabpanel" aria-label={activeTab === 'courses' ? 'Courses' : 'Professors'}>
        {active.results.map(result => {
          const selection = asResult(activeTab === 'courses' ? result : { ...result, type: 'professor' });
          return (
            <button key={selection.id} className="result-item" disabled={resolving} onClick={() => onResultSelect(selection, intent)}>
              <span className={`result-type result-type-${selection.type}`}>{selection.type === 'course' ? 'Course' : 'Professor'}</span>
              {selection.type === 'course' && <span className="course-code">{result.course_code}</span>}
              <span className="course-name">{selection.type === 'course' ? result.course_name : result.name}</span>
            </button>
          );
        })}
      </div>
      {isLoading && <div className="loading-message">Loading more results...</div>}
      {active.results.length < active.total_count && !isLoading && <button onClick={loadMore} className="load-more-button">Show More Results ({active.total_count - active.results.length} remaining)</button>}
      {active.results.length >= active.total_count && <div className="end-message">All results displayed</div>}
    </div>
  );
};
export default SearchResults;
