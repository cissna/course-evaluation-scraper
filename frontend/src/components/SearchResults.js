import React, { useState, useEffect } from 'react';
import './SearchResults.css';
import { API_BASE_URL } from '../config';

const SearchResults = ({ searchQuery, onCourseSelect, onBack }) => {
    const [results, setResults] = useState([]);
    const [totalCount, setTotalCount] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const resultsPerPage = 20;

    useEffect(() => {
        if (searchQuery) {
            fetchResults(1);
        }
    }, [searchQuery]);

    const fetchResults = async (page) => {
        setIsLoading(true);
        setError(null);

        const offset = (page - 1) * resultsPerPage;

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/search/course_name_detailed/${encodeURIComponent(searchQuery)}?limit=${resultsPerPage}&offset=${offset}`
            );

            if (!response.ok) {
                throw new Error('Failed to fetch search results');
            }

            const data = await response.json();
            setResults(data.results);
            setTotalCount(data.total_count);
            setCurrentPage(page);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLoadMore = () => {
        const nextPage = currentPage + 1;
        fetchResults(nextPage);
    };

    const handleCourseClick = (result) => {
        // If it's a grouped course, select the primary course that matched the search
        // Otherwise, use the course code directly
        const courseToSelect = result.primary_course || result.course_code;
        onCourseSelect(courseToSelect);
    };

    const currentResultCount = currentPage * resultsPerPage;
    const hasMore = currentResultCount < totalCount;

    return (
        <div className="search-results">
            <div className="search-results-header">
                <button onClick={onBack} className="back-button">
                    ← Back to Search
                </button>
                <h2>Search Results for "{searchQuery}"</h2>
                <p className="results-count">
                    {totalCount > 0 ? (
                        <>Showing {Math.min(currentResultCount, totalCount)} of {totalCount} results</>
                    ) : (
                        'No results found'
                    )}
                </p>
            </div>

            {error && (
                <div className="error-message">
                    Error: {error}
                </div>
            )}

            <div className="results-list">
                {results.map((course, index) => (
                    <div
                        key={course.primary_course || course.course_code || index}
                        className="result-item"
                        onClick={() => handleCourseClick(course)}
                    >
                        <div className="course-code">{course.course_code}</div>
                        <div className="course-name">{course.course_name}</div>
                    </div>
                ))}
            </div>

            {isLoading && (
                <div className="loading-message">
                    Loading results...
                </div>
            )}

            {hasMore && !isLoading && (
                <button
                    onClick={handleLoadMore}
                    className="load-more-button"
                >
                    Show More Results ({totalCount - currentResultCount} remaining)
                </button>
            )}

            {!hasMore && results.length > 0 && (
                <div className="end-message">
                    All results displayed
                </div>
            )}
        </div>
    );
};

export default SearchResults;