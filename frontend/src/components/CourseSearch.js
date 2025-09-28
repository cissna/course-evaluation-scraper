import React, { useState, useRef } from 'react';
import './CourseSearch.css';
import { API_BASE_URL } from '../config';
import SearchHistory from './SearchHistory';
import { getSearchHistory } from '../utils/storageUtils';

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

const CourseSearch = ({ onDataReceived, onMultipleResults, onLoadingChange, currentCourseCode }) => {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [lastSearchedQuery, setLastSearchedQuery] = useState('');
    const [showHistory, setShowHistory] = useState(false);
    const searchInputRef = useRef(null);

    const filteredHistory = getFilteredHistory(getSearchHistory(), query, currentCourseCode);
    const willShowDropdown = showHistory && filteredHistory.length > 0;

    const handleSearch = async (searchQuery) => {
        const finalQuery = searchQuery || query;
        if (!finalQuery.trim()) return;
        const trimmedQuery = finalQuery.trim().substring(0, 1000);
        setLastSearchedQuery(trimmedQuery);
        setIsLoading(true);
        setError(null);
        setShowHistory(false);

        const courseCodePattern = /^[A-Za-z]{2}\.\d{3}\.\d{3}$/;
        const isCourseCode = courseCodePattern.test(trimmedQuery);

        try {
            let courseCode;
            if (isCourseCode) {
                courseCode = trimmedQuery.toUpperCase();
            } else {
                if (onLoadingChange) onLoadingChange(true);
                const searchResponse = await fetch(`${API_BASE_URL}/api/search/course_name/${trimmedQuery}`);
                if (!searchResponse.ok) throw new Error('Error searching for course name.');
                
                const courseCodes = await searchResponse.json();
                if (courseCodes.length === 0) throw new Error('No matching courses found. Try a course code.');
                if (courseCodes.length === 1) {
                    courseCode = courseCodes[0];
                } else {
                    // Multiple results - route to search results page
                    if (onMultipleResults) {
                        onMultipleResults(trimmedQuery);
                        return;
                    } else {
                        // Fallback to first result if onMultipleResults not provided
                        courseCode = courseCodes[0];
                    }
                }
            }
            onDataReceived(courseCode);
        } catch (err) {
            setError(err.message);
            onDataReceived(null);
        } finally {
            setIsLoading(false);
            if (!isCourseCode && onLoadingChange) onLoadingChange(false);
        }
    };

    const handleHistoryItemClick = (courseCode) => {
        setQuery(courseCode);
        handleSearch(courseCode);
    };

    return (
        <div className="course-search">
            <div className="search-input-container">
                <input
                    ref={searchInputRef}
                    type="text"
                    value={query}
                    maxLength="1000"
                    className={willShowDropdown ? "dropdown-visible" : undefined}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && query.trim() !== '' && query.trim() !== lastSearchedQuery) {
                            handleSearch();
                        }
                    }}
                    onFocus={() => setShowHistory(true)}
                    onClick={() => setShowHistory(true)}
                    placeholder="Enter course code or name (e.g., AS.180.101 or Introduction to Psych)"
                />
                <SearchHistory
                    isOpen={showHistory}
                    onClose={() => setShowHistory(false)}
                    onItemClick={handleHistoryItemClick}
                    searchValue={query}
                    currentCourseCode={currentCourseCode}
                    anchorRef={searchInputRef}
                />
            </div>
            <button onClick={() => handleSearch()} disabled={isLoading}>
                {isLoading ? 'Searching...' : 'Search'}
            </button>
            {error && <p className="error-message">{error}</p>}
        </div>
    );
};

export default CourseSearch;